from typing import\
    Type,\
    Generic,\
    Optional,\
    TypeVar,\
    get_args,\
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
    ModelValidateFieldsBaseTypeNode,\
    ModelDiscardMetaInstancesFromInheritedFieldsNode,\
    ModelValidateSameTypeMetaInstancesHaveDifferentNamesNode,\
    ModelExtractCheckConstraintsNode
from .composite import\
    pg_composite
from .enums import\
    pg_enum
from .builtin import\
    pg_builtin
from ..inspection import\
    extract_by_instance_type_from_model_fields_info,\
    aggregate,\
    ordered_set_accumulator,\
    set_accumulator,\
    key_by,\
    extract_first_instance_from_field_metadata,\
    extract_inherited_fields,\
    is_optional,\
    extract_by_instance_type_from_field_info,\
    extract_type,\
    extract_definition_fields
from .common.meta import\
    pg_check,\
    pg_default_value,\
    pg_comment,\
    OperandDefinitionContext
from .sequence import\
    pg_sequence
from ..extraction.base import\
    pg_table_index_type,\
    pg_table_foreign_key_action

# KNOWN BUGS
# BUG: if two parent table share the same value of the same type, and each one sets a different default value, then postgres will raise a conflict error, breaking the transaction. wont be implemented in this first version.


T = TypeVar("T")


@dataclass(kw_only=True)
class pg_table_index:
    name: str
    type: pg_table_index_type = pg_table_index_type.BTREE


@dataclass(kw_only=True)
class pg_table_unique_index:
    name: str
    type: pg_table_index_type = pg_table_index_type.BTREE


@dataclass(kw_only=True)
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
        if not issubclass(self.other_class, pg_table):
            raise TypeError(f'Other class {self.other_class} must be a {pg_table} instance')
        if self.other_class_column_name not in self.other_class.model_fields:
            raise TypeError(f'Foreign key column {self.other_class_column_name} must exist in {self.other_class} definition')
        other_class_column: FieldInfo = self.other_class.model_fields[self.other_class_column_name]
        if extract_type(other_class_column.annotation) != extract_type(source):
            raise TypeError(f'Foreign key column {handler.field_name} type must match with {self.other_class_column_name} in {self.other_class} definition')
        schema: core_schema.CoreSchema = handler(source)
        # ignore class pg_check[T] has no attribute __orig_class__ error
        # raised by mypy
        return schema


@dataclass(kw_only=True)
class pg_default_sequence_nextval:
    seq: pg_sequence

    def __get_pydantic_core_schema__(self, source: type, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        base_seq: type = getattr(self.seq, '__pg_definition')()['base_type']
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
        # if value is None:
        #    raise ValueError(f'Sequence {self.seq.__name__} value cant be empty')
        definition = getattr(self.seq, '__pg_definition')()
        if definition['min_value'] is not None and definition['min_value'] > value:
            raise ValueError('Value cant be less than sequence min value')
        if definition['max_value'] is not None and definition['max_value'] < value:
            raise ValueError('Value cant be greater than sequence max value')
        return value


table_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(pg_table_definition_flow_root)


class _TableValidateConsistentBaseClassesNode(SingleChoiceDefinitionFlowNode):
    """
    We must ensure that target definition inherits from classes with the same 
    base class. Also we must validate that base classes columns/fields wont
    collide between them.
    """

    def __init__(self):
        super().__init__('table-validate-consistent-base-classes-node')

    def add_field_types(self, from_cls: type, acc: Optional[dict[str, type]] = None) -> dict[str, set[type]]:
        acc = {} if acc is None else acc
        for field, info in from_cls.model_fields.items():
            fset: set[type] = acc.get(field, set())
            fset.add(info.annotation)
            acc[field] = fset
        return acc

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        field_types: dict[str, set[type]] = dict()
        has_more_than_one_base: bool = len(target.__bases__) > 1
        field_types = self.add_field_types(target, None)
        for base_class in target.__bases__:
            if not issubclass(base_class, pg_table):
                errors.append(f'Inherited class {base_class} must be a subclass of {pg_table}')
                continue
            elif has_more_than_one_base and base_class == pg_table:
                errors.append(f'Cant define {pg_table} as base class if {target} is set to inherit more than one base class')
            field_types = self.add_field_types(base_class, field_types)
        for field in field_types:
            if len(field_types[field]) > 1:
                base_cls_str: str = ', '.join([str(f) for f in field_types[field]])
                errors.append(f'Field {field} type conflict. Declared in multiple base classes: {base_cls_str}')
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


class _TableValidateMutuallyExclusiveMetadataNode(SingleChoiceDefinitionFlowNode):
    """
    We must ensure that target definition fields has no two metadata instances indicated by mutually_exclusive pairs at the same time.
    """

    def __init__(self):
        super().__init__('table-validate-mutually-exclusive-metadata-node')
        self.mutually_exclusive: list[tuple[type, type]] = [
            (pg_default_value, pg_default_sequence_nextval)]

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        for field, info in target.model_fields.items():
            for tp1, tp2 in self.mutually_exclusive:
                tp1inst: Optional[Any] = extract_first_instance_from_field_metadata(info, tp1)
                tp2inst: Optional[Any] = extract_first_instance_from_field_metadata(info, tp2)
                if tp1inst is not None and tp2inst is not None:
                    errors.append(f'Field {field} described by two mutually exclusive metadata instances: {repr(tp2inst)} and {repr(tp2inst)}')
        if len(errors) > 0:
            raise FlowNodeException(self.name, errors)


class _TableValidateSameTypeMetaInstancesHaveDifferentNamesNode(ModelValidateSameTypeMetaInstancesHaveDifferentNamesNode):
    def __init__(self):
        super().__init__('table-validate-same-type-meta-instances-have-different-names-node',
                         types=[pg_check, pg_table_unique_index, pg_table_index])


class _TableValidateRestrictedMetadataTypesNode(ModelValidateRestrictedMetadataTypesNode):
    def __init__(self):
        super().__init__('table-validate-restricted-metadata-types-node',
                         types=[pg_table_foreign_key, pg_table_primary_key, pg_table_index,
                                pg_table_unique_index, pg_check, pg_default_value,
                                pg_default_sequence_nextval, pg_comment])


class _TableValidateUniqueMetadataTypesNode(ModelValidateUniqueMetadataTypesNode):
    def __init__(self):
        super().__init__('table-validate-unique-metadata-types-node',
                         types=[pg_table_foreign_key, pg_table_primary_key, pg_default_value,
                                pg_default_sequence_nextval, pg_comment])


class _TableValidateFieldsBaseTypeNode(ModelValidateFieldsBaseTypeNode):
    def __init__(self):
        super().__init__('table-validate-fields-base-type-node',
                         type_subclass=[pg_enum, pg_builtin, pg_composite],
                         type_instance=[pg_builtin])


class _TableValidateSameTypeMetaInstancesHaveDifferentNamesNode(ModelValidateSameTypeMetaInstancesHaveDifferentNamesNode):
    def __init__(self):
        super().__init__('table-validate-same-type-meta-instances-have-different-names-node',
                         types=[pg_check, pg_table_unique_index, pg_table_index])


class _TableDependsOnValidationNodes:
    def get_dependencies(self) -> tuple[str]:
        return ('table-validate-consistent-base-classes-node',
                'table-validate-mutually-exclusive-metadata-node',
                'table-validate-restricted-metadata-types-node',
                'table-validate-unique-metadata-types-node',
                'table-validate-same-type-meta-instances-have-different-names-node',
                'table-validate-fields-base-type-node',
                'table-merge-inherited-fields-node',
                'table-validate-existing-columns-node')


class _TableExtractIndexesNode(SingleChoiceDefinitionFlowNode,
                               _TableDependsOnValidationNodes):
    def __init__(self):
        super().__init__('table-extract-indexes-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        indexes: list[dict[str, Any]] = [ix for _, ix in extract_by_instance_type_from_model_fields_info(
            target,
            pg_table_index,
            lambda field_name, index: {
                'column_name': field_name,
                'type':   index.type,
                'name':   index.name})]
        try:
            grouped_by_name: dict[str, list[dict[str, Any]]] = key_by(
                ('name', ),
                indexes)
            definition: list[dict[str, Any]] = [aggregate(grouped_by_name[ix_name], {'column_name': set_accumulator}) for ix_name in grouped_by_name]
            accumulator.add_definition('indexes', definition if len(definition) > 0 else None)
        except Exception as e:
            raise FlowNodeException(self.name, [str(e)])


class _TableExtractUniqueIndexesNode(SingleChoiceDefinitionFlowNode,
                                     _TableDependsOnValidationNodes):
    def __init__(self):
        super().__init__('table-extract-unique-indexes-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        uixs: list[dict[str, Any]] = [uix for _, uix in extract_by_instance_type_from_model_fields_info(
            target,
            pg_table_unique_index,
            lambda field_name, uix: {
                'column_name': field_name,
                'type':        uix.type,
                'name':        uix.name})]
        try:
            grouped_by_name: dict[str, list[dict[str, Any]]] = key_by(
                ('name', ),
                uixs)
            definition: list[dict[str, Any]] = [aggregate(grouped_by_name[uix_name], {'column_name': set_accumulator}) for uix_name in grouped_by_name]
            accumulator.add_definition('unique_indexes', definition if len(definition) > 0 else None)
        except Exception as e:
            raise FlowNodeException(self.name, [str(e)])


class _TableExtractPrimaryKeyNode(SingleChoiceDefinitionFlowNode,
                                  _TableDependsOnValidationNodes):
    def __init__(self):
        super().__init__('table-extract-primary-key-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        pks: list[dict[str, Any]] = [pk for _, pk in extract_by_instance_type_from_model_fields_info(
            target,
            pg_table_primary_key,
            lambda field_name, pk: {
                'column_name': field_name,
                'name':   pk.name})]
        try:
            grouped_by_name: dict[str, list[dict[str, Any]]] = key_by(
                ('name', ),
                pks)
            definition: Optional[list[dict[str, Any]]] = [aggregate(grouped_by_name[pk_name], {'column_name': set_accumulator}) for pk_name in grouped_by_name]
            if len(definition) > 1:
                raise Exception(f'Multiple primary keys detected for class {target}')
            elif len(definition) == 1:
                accumulator.add_definition('primary_key', definition[0])
        except Exception as e:
            raise FlowNodeException(self.name, [str(e)])


class _TableExtractForeignKeysNode(SingleChoiceDefinitionFlowNode,
                                   _TableDependsOnValidationNodes):
    def __init__(self):
        super().__init__('table-extract-foreign-keys-node')

    def _extract_other_class_constraints(
        self, fk: dict[str, Any], constraint_names: tuple[str, ...]
    ) -> list[dict[str, Any]]:
        other_class_pg_def: Optional[dict[str, Any]] = getattr(fk['other_class'], '__pg_definition')()
        res: list[dict[str, Any]] = []
        for name in constraint_names:
            if other_class_pg_def[name] is not None:
                if isinstance(other_class_pg_def[name], list):
                    res += other_class_pg_def[name]
                else:
                    res.append(other_class_pg_def[name])
        return res

    def _check_for_other_class_constraints(
        self, fks: list[dict[str, Any]],
        constraint_names: tuple[str, ...]
    ) -> list[str]:
        errors: list[str] = []
        for fk in fks:
            constraints: list[dict[str, Any]] = self._extract_other_class_constraints(fk, constraint_names)
            class_column_names = set([const[0] for const in fk['constrained_column_pairs']])
            other_class_column_names = set([const[1] for const in fk['constrained_column_pairs']])
            if len(constraints) == 0 or not any([const['column_name'] == other_class_column_names for const in constraints]):
                errors.append(f'Foreign key {fk["name"]} error: Other class {fk["other_class"]} must define any {constraint_names} constraint over referenced columns {other_class_column_names}')
        if len(errors) > 0:
            raise FlowNodeException(self.name, errors)

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        fks: list[dict[str, Any]] = [fk for _, fk in extract_by_instance_type_from_model_fields_info(
            target,
            pg_table_foreign_key,
            lambda field_name, fk: {
                'name':                     fk.name,
                'other_class':              fk.other_class,
                'constrained_column_pairs': (field_name, fk.other_class_column_name, ),
                'on_update':                fk.on_update,
                'on_delete':                fk.on_delete})]
        errors: list[str] = []
        try:
            grouped_by_name: dict[str, list[dict[str, Any]]] = key_by(
                ('name', ),
                fks)
            definition: list[dict[str, Any]] = [aggregate(grouped_by_name[fk_name], {
                    'constrained_column_pairs': set_accumulator}) for fk_name in grouped_by_name]
            self._check_for_other_class_constraints(definition, ('unique_indexes', 'primary_key', ))
            accumulator.add_definition('foreign_keys', definition if len(definition) > 0 else None)
        except FlowNodeException as e:
            raise e
        except Exception as e:
            raise FlowNodeException(self.name, [str(e)])


class _TableExtractCheckConstraintsNode(ModelExtractCheckConstraintsNode):
    def __init__(self):
        super().__init__('table-extract-check-constraints-node',
                         OperandDefinitionContext.TABLE)


class _TableExtractColumnsNode(SingleChoiceDefinitionFlowNode, _TableDependsOnValidationNodes):
    def __init__(self):
        super().__init__('table-extract-column-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        # extraer las definiciones de columna
        columns: list[dict[str, Any]] = []
        for name, info in extract_definition_fields(target):
            col_data: dict[str, Any] = {
                'name': name,
                'type': info.annotation}
            comment: Optional[pg_comment] = extract_first_instance_from_field_metadata(info, pg_comment)
            col_data['comment'] = comment
            default_value: Optional[pg_default_value | pg_default_sequence_nextval] = extract_first_instance_from_field_metadata(info, pg_default_value)
            if default_value is not None:
                default_value.default.propagate_definition(target.model_fields[name].annotation, name, OperandDefinitionContext.TABLE)
            else:
                default_value = extract_first_instance_from_field_metadata(info, pg_default_sequence_nextval)
            col_data['default_value'] = default_value
            columns.append(col_data)
        accumulator.add_definition('columns', columns)


class _TableDiscardMetaInstancesFromInheritedFieldsNode(ModelDiscardMetaInstancesFromInheritedFieldsNode):
    def __init__(self):
        super().__init__('table-discard-meta-instances-from-inherited-fields-node')


class _TableStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('table-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Any] = dict()
        definition['class'] = target
        definition['base_classes'] = set(target.__bases__) if len(target.__bases__) > 1 else None
        definition['comment'] = None
        definition['columns'] = accumulator.get_definition('columns', 'extraction')
        definition['primary_key'] = accumulator.get_definition('primary_key', 'extraction')
        definition['foreign_keys'] = accumulator.get_definition('foreign_keys', 'extraction')
        definition['unique_indexes'] = accumulator.get_definition('unique_indexes', 'extraction')
        definition['indexes'] = accumulator.get_definition('indexes', 'extraction')
        definition['check'] = accumulator.get_definition('check_constraints', 'extraction')
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('table-extract-indexes-node',
                'table-extract-primary-key-node',
                'table-extract-foreign-keys-node',
                'table-extract-unique-indexes-node',
                'table-extract-check-constraints-node',
                'table-discard-meta-instances-from-inherited-fields-node',
                'table-extract-column-definition-node')


table_flow_builder\
    .at_work_path('validation')\
        .add_node(_TableValidateConsistentBaseClassesNode)\
        .add_node(_TableValidateExistingColumnsNode)\
        .add_node(_TableValidateMutuallyExclusiveMetadataNode)\
        .add_node(_TableValidateSameTypeMetaInstancesHaveDifferentNamesNode)\
        .add_node(_TableValidateRestrictedMetadataTypesNode)\
        .add_node(_TableValidateUniqueMetadataTypesNode)\
        .add_node(_TableValidateFieldsBaseTypeNode)\
    .at_work_path('extraction')\
        .add_node(_TableExtractIndexesNode).critical()\
        .add_node(_TableExtractPrimaryKeyNode)\
        .add_node(_TableExtractForeignKeysNode)\
        .add_node(_TableExtractUniqueIndexesNode)\
        .add_node(_TableExtractCheckConstraintsNode)\
        .add_node(_TableExtractColumnsNode)\
        .add_node(_TableDiscardMetaInstancesFromInheritedFieldsNode)\
    .at_work_path('')\
        .add_node(_TableStoreFinalDefinitionNode).critical()


__all__ = {'pg_table': pg_table}
