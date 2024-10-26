from typing import\
    Type,\
    Generic,\
    Optional,\
    TypeVar,\
    Any
from dataclasses import\
    dataclass
from pydantic_core import\
    core_schema
from pydantic import\
    GetCoreSchemaHandler,\
    ValidationInfo
from pydantic.fields import\
    FieldInfo
from .common.flow import\
    SingleChoiceDefinitionFlowNode,\
    FlowAccumulator,\
    FlowNodeException,\
    DefinitionFlowBuilder
from .common.model import\
    pg_table,\
    pg_table_definition_flow_root,\
    ModelValidateRestrictedMetadataTypesNode,\
    ModelValidateUniqueMetadataTypesNode,\
    ModelValidateFieldsBaseTypeNode
from .composite import\
    pg_composite
from .enums import\
    pg_enum
from .builtin import\
    pg_builtin
from ..extraction.base import\
    pg_column_definition,\
    pg_foreign_key_definition,\
    pg_primary_key_definition,\
    pg_index_definition
from ..inspection import\
    extract_by_instance_type_from_model_fields_info,\
    aggregate,\
    ordered_set_accumulator,\
    key_by,\
    extract_first_instance_from_field_metadata,\
    is_optional,\
    extract_type
from .common.meta import\
    pg_check,\
    pg_default_value,\
    pg_comment
from .sequence import\
    pg_sequence
from ..extraction.base import\
    pg_table_index_type,\
    pg_table_foreign_key_action


T = TypeVar("T")


@dataclass
class pg_table_index:
    name: str
    type: pg_table_index_type = pg_table_index_type.BTREE


@dataclass
class pg_table_unique_index:
    name: str
    type: pg_table_index_type = pg_table_index_type.BTREE


@dataclass
class pg_table_primary_key:
    name: str


@dataclass(kw_only=True)
class pg_table_foreign_key:
    name: str
    other_class: type[pg_table]
    other_class_column_name: str
    on_update: pg_table_foreign_key_action = pg_table_foreign_key_action.NO_ACTION
    on_delete: pg_table_foreign_key_action = pg_table_foreign_key_action.NO_ACTION

    def __get_pydantic_core_schema__(self, source: Type[T], handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        errors: list[str] = []
        if not issubclass(self.other_class, pg_table):
            errors.append(f'Other class {self.other_class} must be a {pg_table} instance')
        if self.other_class_column_name not in self.other_class.model_fields:
            errors.append(f'Foreign key column {self.other_class_column_name} must exist in {self.other_class} definition')
        other_class_column: FieldInfo = self.other_class.model_fields[self.other_class_column_name]
        schema: core_schema.CoreSchema = handler(source)
        if extract_type(other_class_column.annotation) != extract_type(source):
            errors.append(f'Foreign key column {handler.field_name} type must match with {self.other_class_column_name} in {self.other_class} definition')
        if len(errors) > 0:
            raise TypeError(', '.join(errors))
        # ignore class pg_check[T] has no attribute __orig_class__ error
        # raised by mypy
        return schema


class pg_default_sequence_nextval(Generic[T]):
    seq: pg_sequence

    def __get_pydantic_core_schema__(self, source: type, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        base_seq: type = self.seq.__bases__[0]
        errors: list[str] = []
        if is_optional(source):
            errors.append('Annotated type must not be optional')
        if base_seq is not source:
            errors.append('Sequence type must match annotated type')
        if len(errors) > 0:
            raise TypeError(', '.join(errors))
        # ignore class pg_table_meta.check[T] has no attribute __orig_class__ error
        # raised by mypy
        return core_schema.with_info_after_validator_function(
            function=self.validate,
            schema=handler(source),
            field_name=handler.field_name)

    def validate(self, value: Any, info: ValidationInfo) -> Any:
        if value is None:
            raise ValueError(f'Sequence {self.seq.__name__} value cant be empty')
        return value


table_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(pg_table_definition_flow_root)


# una tabla puede heredar unicamente de otra tabla
# class _TableValidateTypeInheritanceNode(SingleChoiceDefinitionFlowNode[T]):
#     """
#     Las clases pueden tener herencia cruzada por ejemplo heredar de un composite y table
#     a la vez, esto es ilegal, esta validacion la corremos al momento de definir el 
#     core_schema de pydantic para asegurarnos que el PGRepresentable es valido y 
#     su definicion univoca
#     """
# 
#     def __init__(self, base_class: type):
#         super().__init__('validate-type-inheritance-node')
# 
#     def execute(self, cls: type, accumulator: FlowAccumulator) -> None:
#         pass
class _TableValidateConsistentBaseClassesNode(SingleChoiceDefinitionFlowNode):
    """
    We must ensure that target definition inherits from classes with the same 
    base class. Also we must validate that base classes columns/fields wont
    collide between them.
    """

    def __init__(self):
        super().__init__('table-validate-consistent-base-classes-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        field_dict: dict[str, set[type]] = dict()
        for base_class in target.__bases__:
            if not issubclass(base_class, pg_table):
                errors.append(f'Inherited class {base_class} must be a subclass of {pg_table}')
                continue
            for field in base_class.model_fields:
                fset: set[type] = field_dict.get(field, set())
                fset.add(base_class)
                field_dict[field] = fset
        for field in target.model_fields:
            fset: set[type] = field_dict.get(field, set())
            fset.add(base_class)
            field_dict[field] = fset
        for field in field_dict:
            if len(field_dict[field]) > 1:
                base_cls_str: str = ', '.join(field_dict[field])
                errors.append(f'Field {field} declared in multiple base classes: {base_cls_str}')
        if len(errors) > 0:
            raise FlowNodeException(self.name, errors)


class _TableValidateExistingColumnsNode(SingleChoiceDefinitionFlowNode):
    """
    We must ensure that target definition has fields
    """

    def __init__(self):
        super().__init__('table-validate-existing-columns-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        if len(target.model_fields.keys()) <= 0:
            raise FlowNodeException(self.name, [f'Class {target} must define columns.'])


class _TableValidateRestrictedMetadataTypesNode(ModelValidateRestrictedMetadataTypesNode):
    def __init__(self):
        super().__init__('table-validate-existing-columns-node',
                         [pg_table_foreign_key,
                          pg_table_primary_key,
                          pg_table_index,
                          pg_table_unique_index,
                          pg_check,
                          pg_default_value,
                          pg_default_sequence_nextval,
                          pg_comment])


class _TableValidateUniqueMetadataTypesNode(ModelValidateUniqueMetadataTypesNode):
    def __init__(self):
        super().__init__('table-validate-existing-columns-node',
                         [pg_table_foreign_key,
                          pg_table_primary_key,
                          pg_default_value,
                          pg_default_sequence_nextval,
                          pg_comment,
                          pg_check])


class _TableValidateFieldsBaseTypeNode(ModelValidateFieldsBaseTypeNode):
    def __init__(self):
        super().__init__('table-validate-existing-columns-node',
                         type_subclass=[pg_enum,
                                        pg_builtin,
                                        pg_composite],
                         type_instance=[pg_builtin])


class _TableDependsOnValidationNodes:
    def get_dependencies(self) -> tuple[str]:
        return ('table-validate-consistent-base-classes-node',
                'table-validate-restricted-metadata-types-node',
                'table-validate-unique-metadata-types-node',
                'table-validate-fields-base-type-node',
                'table-merge-inherited-fields-node',
                'table-validate-existing-columns-node')


class _TableExtractIndexDefinitionFromDeclarationNode(SingleChoiceDefinitionFlowNode,
                                                      _TableDependsOnValidationNodes):
    """
    It used to inherit from a class called ValidatesConflictingDefinitions to check if any indexes
    had been injected through private properties, but in case we decide to implement direct 
    (not inferred) index definition, then it will be done via decorators, and it wont be detected
    by this flow
    """

    def __init__(self):
        super().__init__('table-extract-index-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        indexes: list[dict[str, Any]] = [ix for ix in extract_by_instance_type_from_model_fields_info(
            target,
            pg_table_index,
            lambda field_name, index: {
                'column_name': field_name,
                'type':   index.type,
                'name':   index.name,
                'is_unique': False})]
        try:
            grouped_by_name: dict[str, list[dict[str, Any]]] = key_by(
                ('name', ),
                indexes)
            definition: list[dict[str, Any]] = [aggregate(grouped_by_name[ix_name], {
                    'column_name': ordered_set_accumulator}) for ix_name in grouped_by_name]
            if len(definition) <= 0:
                return
            accumulator.add_definition('indexes', definition)
        except Exception as e:
            raise FlowNodeException(self.name, [str(e)])


class _TableExtractPrimaryKeyDefinitionFromDeclarationNode(SingleChoiceDefinitionFlowNode,
                                                           _TableDependsOnValidationNodes):
    """
    It used to inherit from a class called ValidatesConflictingDefinitions to check if any indexes
    had been injected through private properties, but in case we decide to implement direct 
    (not inferred) index definition, then it will be done via decorators, and it wont be detected
    by this flow
    """

    def __init__(self):
        super().__init__('table-extract-primary-key-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        pks: list[dict[str, Any]] = [pk for pk in extract_by_instance_type_from_model_fields_info(
            target,
            pg_table_primary_key,
            lambda field_name, pk: {
                'column_name': field_name,
                'name':   pk.name})]
        try:
            grouped_by_name: dict[str, list[dict[str, Any]]] = key_by(
                ('name', ),
                pks)
            definition: list[dict[str, Any]] = [aggregate(grouped_by_name[pk_name], {
                    'column_name': ordered_set_accumulator}) for pk_name in grouped_by_name]
            if len(definition) <= 0:
                return
            accumulator.add_definition('primary_key', definition)
        except Exception as e:
            raise FlowNodeException(self.name, [str(e)])


class _TableExtractForeignKeyDefinitionFromDeclarationNode(SingleChoiceDefinitionFlowNode,
                                                           _TableDependsOnValidationNodes):
    """
    It used to inherit from a class called ValidatesConflictingDefinitions to check if any indexes
    had been injected through private properties, but in case we decide to implement direct 
    (not inferred) index definition, then it will be done via decorators, and it wont be detected
    by this flow
    """

    def __init__(self):
        super().__init__('table-extract-foreign-keys-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        fks: list[dict[str, Any]] = [fk for fk in extract_by_instance_type_from_model_fields_info(
            target,
            pg_table_foreign_key,
            lambda field_name, fk: {
                'name':                    fk.name,
                'other_class_name':        fk.other_class.__name__,
                'other_class_column_name': fk.other_class_column_name,
                'on_update':               fk.on_update,
                'on_delete':               fk.on_delete,
                'class_column_name':       field_name})]
        try:
            grouped_by_name: dict[str, list[dict[str, Any]]] = key_by(
                ('name', ),
                fks)
            definition: list[dict[str, Any]] = [aggregate(grouped_by_name[fk_name], {
                    'class_column_name': ordered_set_accumulator,
                    'other_class_column_name': ordered_set_accumulator}) for fk_name in grouped_by_name]
            if len(definition) <= 0:
                return
            accumulator.add_definition('foreign_keys', definition)
        except Exception as e:
            raise FlowNodeException(self.name, [str(e)])


class _TableExtractUniqueIndexDefinitionFromDeclarationNode(SingleChoiceDefinitionFlowNode,
                                                            _TableDependsOnValidationNodes):
    """
    It used to inherit from a class called ValidatesConflictingDefinitions to check if any indexes
    had been injected through private properties, but in case we decide to implement direct 
    (not inferred) index definition, then it will be done via decorators, and it wont be detected
    by this flow
    """

    def __init__(self):
        super().__init__('table-extract-unique-indexes-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        uixs: list[dict[str, Any]] = [uix for uix in extract_by_instance_type_from_model_fields_info(
            target,
            pg_table_unique_index,
            lambda field_name, uix: {
                'column_name': field_name,
                'type':        uix.type,
                'name':        uix.name,
                'is_unique':   True})]
        try:
            grouped_by_name: dict[str, list[dict[str, Any]]] = key_by(
                ('name', ),
                uixs)
            definition: list[dict[str, Any]] = [aggregate(grouped_by_name[uix_name], {
                    'column_name': ordered_set_accumulator}) for uix_name in grouped_by_name]
            if len(definition) <= 0:
                return
            accumulator.add_definition('unique_indexes', definition)
        except Exception as e:
            raise FlowNodeException(self.name, [str(e)])


class _TableExtractInheritanceDefinitionFromDeclarationNode(SingleChoiceDefinitionFlowNode,
                                                            _TableDependsOnValidationNodes):
    def __init__(self):
        super().__init__('table-extract-base-classes-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        try:
            inherited: list[type] = target.__bases__
            if len(inherited) > 0:
                accumulator.add_definition('inherited', inherited)
        except Exception as e:
            raise FlowNodeException(self.name, [str(e)])


class _TableExtractColumnDefinitionFromDeclarationNode(SingleChoiceDefinitionFlowNode,
                                                       _TableDependsOnValidationNodes):
    def __init__(self):
        super().__init__('table-extract-columns-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        # extraer las definiciones de columna
        columns: list[dict[str, Any]] = []
        ctr: int = 0
        for name, info in target.model_fields.items():
            check: Optional[pg_check] = extract_first_instance_from_field_metadata(info, pg_check)
            col_data: dict[str, Any] = {
                'name': name,
                'type_name': info.annotation.__name__}
            col_data['order'] = ctr
            ctr += 1
            if check is not None:
                col_data['check_constraint'] = check.as_str()
            comment: Optional[pg_comment] = extract_first_instance_from_field_metadata(info, pg_comment)
            col_data['comment'] = comment
            columns.append(col_data)
        if len(columns) <= 0:
            raise FlowNodeException(self.name, [f'Class {target} must declare columns.'])
        accumulator.add_definition('columns', columns)


class _TableStoreExtractedPrimaryKeyNode(SingleChoiceDefinitionFlowNode):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('table-store-primary-key-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('primary_key', 'extraction')

        pk: pg_primary_key_definition = None if definition is None else pg_primary_key_definition(**(definition[0] | {
            'column_name': tuple(definition[0]['column_name'])}))

        @classmethod
        def __pg_primary_key(cls) -> Optional[pg_primary_key_definition]:
            return pk

        accumulator.add_definition('__pg_primary_key', __pg_primary_key)

    def get_dependencies(self) -> tuple[str]:
        return ('table-extract-primary-key-node', )


class _TableStoreExtractedIndexNode(SingleChoiceDefinitionFlowNode):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('table-store-extracted-index-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        ix_definition: list[dict[str, Any]] = accumulator.get_definition('indexes', 'extraction')
        ixs = []
        if ix_definition is not None:
            ixs: list[pg_index_definition] = [pg_index_definition(**(ix | {
                'column_name': tuple(ix['column_name'])})) for ix in definition]
        uix_definition: list[dict[str, Any]] = accumulator.get_definition('unique_indexes', 'extraction')
        if uix_definition is not None:
            uixs: list[pg_index_definition] = [pg_index_definition(**(uix | {
                'column_name': tuple(uix['column_name'])})) for uix in definition]
            ixs += uixs

        if len(ixs) == 0:
            return

        @classmethod
        def __pg_indexes(cls) -> list[pg_index_definition]:
            return ixs

        accumulator.add_definition('__pg_indexes', __pg_indexes)

    def get_dependencies(self) -> tuple[str]:
        return ('table-extract-unique-indexes-node',
                'table-extract-index-node')


class _TableStoreExtractedForeignKeyNode(SingleChoiceDefinitionFlowNode):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('store-extracted-foreign-keys-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('foreign_keys', 'extraction')

        fks: list[pg_foreign_key_definition] = [] if definition is None else [pg_foreign_key_definition(**(fk | {
            'class_column_name': tuple(fk['class_column_name']),
            'other_class_column_name': tuple(fk['other_class_column_name'])})) for fk in definition]

        @classmethod
        def __pg_foreign_keys(cls) -> list[pg_foreign_key_definition]:
            return fks

        accumulator.add_definition('__pg_foreign_keys', __pg_foreign_keys)

    def get_dependencies(self) -> tuple[str]:
        return ('table-extract-foreign-keys-node', )


class _TableStoreExtractedInheritedClassesNode(SingleChoiceDefinitionFlowNode):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('table-store-base-classes-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        base_classes: tuple[type[Any]] = accumulator.get_definition('inherited', 'extraction')

        @classmethod
        def __pg_base_classes(cls) -> tuple[type[Any]]:
            return tuple() if base_classes is None else base_classes

        accumulator.add_definition('__pg_base_classes', __pg_base_classes)

    def get_dependencies(self) -> tuple[str]:
        return ('table-extract-base-classes-node', )


class _TableStoreExtractedColumnsNode(SingleChoiceDefinitionFlowNode):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('table-store-extracted-columns-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('columns', 'extraction')
        columns: list[pg_column_definition] = [pg_column_definition(**col) for col in definition]

        @classmethod
        def __pg_columns(cls) -> list[pg_column_definition]:
            return columns

        accumulator.add_definition('__pg_columns', __pg_columns)

    def get_dependencies(self) -> tuple[str]:
        return ('table-extract-column-definition-node', )


class _TableStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('table-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Any] = accumulator.get_definition('built')
        accumulator.add_definition('final', {} if definition is None else definition)

    def get_dependencies(self) -> tuple[str]:
        return ('table-store-columns-node', )


table_flow_builder\
    .at_work_path('validation')\
        .add_node(_TableValidateExistingColumnsNode)\
        .add_node(_TableValidateExistingColumnsNode)\
        .add_node(_TableValidateExistingColumnsNode)\
        .add_node(_TableValidateConsistentBaseClassesNode)\
        .add_node(_TableValidateRestrictedMetadataTypesNode)\
        .add_node(_TableValidateUniqueMetadataTypesNode)\
        .add_node(_TableValidateFieldsBaseTypeNode)\
    .at_work_path('extraction')\
        .add_node(_TableExtractIndexDefinitionFromDeclarationNode).critical()\
        .add_node(_TableExtractPrimaryKeyDefinitionFromDeclarationNode)\
        .add_node(_TableExtractForeignKeyDefinitionFromDeclarationNode)\
        .add_node(_TableExtractUniqueIndexDefinitionFromDeclarationNode)\
        .add_node(_TableExtractInheritanceDefinitionFromDeclarationNode)\
        .add_node(_TableExtractColumnDefinitionFromDeclarationNode)\
    .at_work_path('')\
        .add_node(_TableStoreExtractedPrimaryKeyNode).critical()\
        .add_node(_TableStoreExtractedIndexNode)\
        .add_node(_TableStoreExtractedForeignKeyNode)\
        .add_node(_TableStoreExtractedInheritedClassesNode)\
        .add_node(_TableStoreExtractedColumnsNode)\
        .add_node(_TableStoreFinalDefinitionNode)

__all__ = {'pg_table': pg_table}
