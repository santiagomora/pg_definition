from typing import\
    Type,\
    Generic,\
    get_args,\
    Optional,\
    TypeVar
from pgdriver.definition.flows import\
    FlowComponent,\
    FlowAccumulator,\
    FlowComponentException
from pgdriver.definition.flows.common import\
    CommonValidateRestrictedMetadataTypesComponent,\
    CommonValidateUniqueMetadataTypesComponent,\
    CommonValidateFieldsBaseTypeComponent,\
    CommonExtractCheckConstraintsComponent,\
    CommonStoreCheckConstraintsComponent,\
    ValidatesConflictingDefinitions
from pgdriver.definition.build import\
    pg_domain,\
    pg_composite,\
    pg_enum,\
    pg_builtin
from pgdriver.definition.extraction.base import\
    pg_column_definition,\
    pg_foreign_key_definition,\
    pg_primary_key_definition,\
    pg_index_definition
from typing import\
    Any
from pgdriver.definition.inspection import\
    extract_by_instance_type_from_model_fields_info,\
    aggregate,\
    ordered_set_accumulator,\
    key_by,\
    extract_by_instance_type_from_inherited_classes,\
    extract_first_instance_from_field_metadata,\
    extract_definition_fields,\
    extract_by_instance_type_from_list,\
    extract_first_appearance_from_list
from pydantic import\
    BaseModel
from pgdriver.definition.flow import\
    DefinitionFlow
from dataclasses import\
    dataclass
from pgdriver.definition.common.meta import\
    check,\
    comment
from pydantic_core import\
    core_schema
from pydantic import\
    GetCoreSchemaHandler,\
    ValidationInfo
from pydantic.fields import\
    FieldInfo
from pgdriver.definition.inspection import\
    is_optional,\
    extract_type
from pgdriver.definition.build import\
    pg_table,\
    pg_sequence
from pgdriver.definition.extraction.base import\
    pg_table_index_type,\
    pg_table_foreign_key_action


T = TypeVar('T')


class pg_table_meta:
    @dataclass
    class index:
        name: str
        type: pg_table_index_type = pg_table_index_type.BTREE

    @dataclass
    class unique_index:
        name: str
        type: pg_table_index_type = pg_table_index_type.BTREE

    @dataclass
    class primary_key:
        name: str

    @dataclass(kw_only=True)
    class foreign_key:
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
            # ignore class pg_table_meta.check[T] has no attribute __orig_class__ error
            # raised by mypy
            return schema

    class check(check):
        pass

    class comment(comment):
        pass

    class default:
        @dataclass
        class value(Generic[T]):
            content: T

            def __get_pydantic_core_schema__(self, source: Type[T], handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
                base: type = get_args(self.__orig_class__)[0]
                errors: list[str] = []
                if not is_optional(source):
                    errors.append('Annotated type must be optional')
                if base not in get_args(source):
                    errors.append('Base type must match annotated type')
                if len(errors) > 0:
                    raise TypeError(', '.join(errors))
                # ignore class pg_table_meta.check[T] has no attribute __orig_class__ error
                # raised by mypy
                return core_schema.with_info_after_validator_function(
                    function=self.validate,
                    schema=handler(source),
                    field_name=handler.field_name)

            def validate(self, value: Optional[T], info: ValidationInfo) -> T:
                if value is None:
                    return self.content
                return value

            @staticmethod
            def consistent_list(elems: list['pg_table_meta.default.value']) -> bool:
                if len(elems) <= 0:
                    return True
                initial: pg_table_meta.default.value = elems[0]
                consistent: bool = True
                for elem in elems:
                    consistent = consistent and elem.value == initial.value
                return consistent

        @dataclass
        class nextval:
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

            @staticmethod
            def consistent_list(elems: list['pg_table_meta.default.nextval']):
                if len(elems) <= 0:
                    return True
                initial: pg_table_meta.default.nexval = elems[0]
                consistent: bool = True
                for elem in elems:
                    consistent = consistent and elem.seq.__name__ != initial.seq.__name__
                return consistent


pg_table_definition_flow: DefinitionFlow = DefinitionFlow('pgdriver-table-definition-flow')


class pg_table(BaseModel):
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        accumulator: FlowAccumulator = FlowAccumulator()
        pg_table_definition_flow.execute(cls, accumulator)


# una tabla puede heredar unicamente de otra tabla
# class TableValidateTypeInheritanceComponent(FlowComponent[T]):
#     """
#     Las clases pueden tener herencia cruzada por ejemplo heredar de un composite y table
#     a la vez, esto es ilegal, esta validacion la corremos al momento de definir el 
#     core_schema de pydantic para asegurarnos que el PGRepresentable es valido y 
#     su definicion univoca
#     """
# 
#     def __init__(self, base_class: type):
#         super().__init__('validate-type-inheritance-component')
# 
#     def execute(self, cls: type, accumulator: FlowAccumulator) -> None:
#         pass
class TableValidateConsistentBaseClassesComponent(FlowComponent):
    """
    We must ensure that target definition inherits from classes with the same 
    base class. Also we must validate that base classes columns/fields wont
    collide between them.
    """

    def __init__(self):
        super().__init__('validate-consistent-base-classes-component')

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
            raise FlowComponentException(self.name, errors)


class TableValidateExistingColumnsComponent(FlowComponent):
    """
    We must ensure that target definition has fields
    """

    def __init__(self):
        super().__init__('validate-existing-columns-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        if len(target.model_fields.keys()) <= 0:
            raise FlowComponentException(self.name, [f'Class {target} must define columns.'])


class TableValidateRestrictedMetadataTypesComponent(CommonValidateRestrictedMetadataTypesComponent):
    pass


class TableValidateUniqueMetadataTypesComponent(CommonValidateUniqueMetadataTypesComponent):
    pass


class TableValidateFieldsBaseTypeComponent(CommonValidateFieldsBaseTypeComponent):
    pass


class TableMergeInheritedFieldsComponent(FlowComponent):
    """
    Pydantic overrides parent fields when redefined on child tables, losing
    parent field metadata, and allowing child models that would be invalid
    parent models.

    'A serious limitation of the inheritance feature is that indexes (including unique constraints) 
    and foreign key constraints only apply to single tables, not to their inheritance children. 
    This is true on both the referencing and referenced sides of a foreign key constraint. '

    Inherited fields must follow postgres rules when inheriting from table:
    - Data type: field type defined in child table must match parent field type
    - Default value: child table must inherit default value from parent, cant 
    define a different one
    - Foreign key: can be redefined, as they will be interpreted as a
    child table primary key
    - Primary key: can be redefined, as they will be interpreted as a
    child table primary key
    - Check constraints: will be merged by conjunction, as a child table 
    instance must be a valid parent table instance. Programmer must avoid mutually 
    exclusive constraints, as they wont be detected
    - Unique index: can be redefined, as they will be interpreted as a
    child table primary key
    """

    def __init__(self):
        super().__init__('merge-inherited-fields-component')

    def _merge_from_parents(self, target: type, overwritten_fields: dict[str, list[Any]], meta_type: type) -> None:
        # meta_type must be mergeable
        for name in overwritten_fields:
            # Extract mergeable from parent meta and merge with that defined in child
            # There is at most one mergeable instance in field metadata, per previous 
            # validations
            mergeable_child_instance: Optional[Any] = extract_first_instance_from_field_metadata(target.model_fields[name], meta_type)
            mergeable_inherited_instances: list[Any] = [c for c in extract_by_instance_type_from_list(overwritten_fields[name], meta_type)]
            if len(mergeable_inherited_instances) <= 0:
                return
            if mergeable_child_instance is None:
                # merges parent instances and then field in child inherits
                # the merged instance
                target.model_fields[name].metadata.append(mergeable_inherited_instances[0].merge(mergeable_inherited_instances[1:]))
            else:
                mergeable_child_instance.merge(mergeable_inherited_instances)

    def _inherit_from_parents(self, target: type, overwritten_fields: dict[str, list[Any]], meta_type: type) -> None:
        # the precondition is that inherited metadata instances are all consistent
        # accross parent classes, otherwise postgres raises an error. this applies 
        # both on default values and sequences
        for name in overwritten_fields:
            # validate default values or set if not defined in current model
            child_defined: Optional[Any] = extract_first_instance_from_field_metadata(target.model_fields[name], meta_type)
            parent_defined: Optional[Any] = extract_first_appearance_from_list(overwritten_fields[name], meta_type)
            if child_defined is None and parent_defined is not None:
                # inherit parent default value
                target.model_fields[name].annotation.append(parent_defined)

    def _validate_consistent_inherited_metadata(self, target: type, overwritten_fields: dict[str, list[Any]], meta_type: type) -> list[str]:
        # Extract default values and validate all equal
        errors: list[str] = []
        for name in overwritten_fields:
            initial: Optional[Any] = extract_first_instance_from_field_metadata(target.model_fields[name], meta_type)
            inherited_meta: list[Any] = extract_by_instance_type_from_list(overwritten_fields[name], meta_type)
            if not meta_type.consistent_list([initial] + inherited_meta if initial is not None else inherited_meta):
                errors.append(f'Inconsistencies detected in inherited field {name} metadata {meta_type}')
        return errors

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        overwritten_fields: dict[str, list[Any]] = dict()
        # We are going to loop over base class fields and extract the instances
        # that need to be merged, considering that at this point the target
        # is well defined
        for name, info in extract_definition_fields(target, pg_table):
            for icls in extract_by_instance_type_from_inherited_classes(target, pg_table):
                if name in icls.model_fields:
                    # Validate fields share the same type
                    if icls.model_fields[name].annotation != info.annotation:
                        errors.append(f'Overwritten field {name} type in {target} must match with type defined in parent class {icls}')
                    info: list[Any] = overwritten_fields.get(name, [])
                    info += icls.model_fields[name].metadata
        # At this point all metadata from inherited fields is in the overwritten_fields 
        # dictionary, we must extract by instance and validate accordingly, or merge the
        # fields there are two possible cases:
        # 1. overridden field doesnt change default value/nextval, then the default 
        # value must pass to child field
        # 2. overridden field changes default value/nextval, this is illegal
        errors += self._validate_consistent_inherited_metadata(target, overwritten_fields, pg_table_meta.default.value)
        errors += self._validate_consistent_inherited_metadata(target, overwritten_fields, pg_table_meta.default.nextval)
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)
        self._merge_from_parents(target, overwritten_fields, pg_table_meta.check)
        self._inherit_from_parents(target, overwritten_fields, pg_table_meta.default.value)
        self._inherit_from_parents(target, overwritten_fields, pg_table_meta.default.nextval)
        target.model_rebuild(force=True)

    def get_dependencies(self) -> tuple[str]:
        return ('validate-consistent-base-classes-component',
                'validate-restricted-metadata-types-component',
                'validate-unique-metadata-types-component',
                'validate-fields-base-type-component',
                'validate-existing-columns-component')


class TableDependsOnValidationComponents:
    def get_dependencies(self) -> tuple[str]:
        return ('validate-consistent-base-classes-component',
                'validate-restricted-metadata-types-component',
                'validate-unique-metadata-types-component',
                'validate-fields-base-type-component',
                'merge-inherited-fields-component',
                'validate-existing-columns-component')


class TableExtractIndexDefinitionFromDeclarationComponent(FlowComponent,
                                                          ValidatesConflictingDefinitions,
                                                          TableDependsOnValidationComponents):
    """
    Table index can be set via decorators or inferred from field metadata
    """

    def __init__(self):
        super().__init__('extract-index-definition-from-declaration-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        indexes: list[dict[str, Any]] = [ix for ix in extract_by_instance_type_from_model_fields_info(
            target,
            pg_table_meta.index,
            self._base_class,
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
            self.check_conflicting_definitions(target, 'indexes')
            accumulator.add_definition('indexes', definition)
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])


class TableExtractPrimaryKeyDefinitionFromDeclarationComponent(FlowComponent,
                                                               ValidatesConflictingDefinitions,
                                                               TableDependsOnValidationComponents):
    # un campo solo puede tener una declaracion de builtin
    def __init__(self):
        super().__init__('extract-primary-key-definition-from-declaration-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        pks: list[dict[str, Any]] = [pk for pk in extract_by_instance_type_from_model_fields_info(
            target,
            pg_table_meta.primary_key,
            self._base_class,
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
            self.check_conflicting_definitions(target, 'primary_key')
            accumulator.add_definition('primary_key', definition)
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])


class TableExtractForeignKeyDefinitionFromDeclarationComponent(FlowComponent,
                                                               ValidatesConflictingDefinitions,
                                                               TableDependsOnValidationComponents):
    # un campo solo puede tener una declaracion de builtin
    def __init__(self):
        super().__init__('extract-foreign-key-definition-from-declaration-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        fks: list[dict[str, Any]] = [fk for fk in extract_by_instance_type_from_model_fields_info(
            target,
            pg_table_meta.foreign_key,
            self._base_class,
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
            self.check_conflicting_definitions(target, 'foreign_keys')
            accumulator.add_definition('foreign_keys', definition)
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])


class TableExtractUniqueIndexDefinitionFromDeclarationComponent(FlowComponent,
                                                                ValidatesConflictingDefinitions,
                                                                TableDependsOnValidationComponents):
    # un campo solo puede tener una declaracion de builtin
    def __init__(self):
        super().__init__('extract-unique-index-definition-from-declaration-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        uixs: list[dict[str, Any]] = [uix for uix in extract_by_instance_type_from_model_fields_info(
            target,
            pg_table_meta.unique_index,
            self._base_class,
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
            self.check_conflicting_definitions(target, 'unique_indexes')
            accumulator.add_definition('unique_indexes', definition)
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])


class TableExtractInheritanceDefinitionFromDeclarationComponent(FlowComponent,
                                                                TableDependsOnValidationComponents):
    # un campo solo puede tener una declaracion de builtin
    def __init__(self):
        super().__init__('extract-inheritance-definition-from-declaration-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        try:
            inherited: list[type] = extract_by_instance_type_from_inherited_classes(
                target,
                pg_table)
            if len(inherited) > 0:
                accumulator.add_definition('inherited', inherited)
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])


class TableExtractColumnDefinitionFromDeclarationComponent(FlowComponent,
                                                           TableDependsOnValidationComponents):
    def __init__(self):
        super().__init__('extract-column-definition-from-declaration-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        # extraer las definiciones de columna
        columns: list[dict[str, Any]] = []
        ctr: int = 0
        for name, info in target.model_fields.items():
            check: Optional[pg_table_meta.check] = extract_first_instance_from_field_metadata(info, pg_table_meta.check)
            col_data: dict[str, Any] = {
                'name': name,
                'type_name': info.annotation.__name__}
            col_data['order'] = ctr
            ctr += 1
            if check is not None:
                col_data['check_constraint'] = check.as_str()
            comment: Optional[pg_table_meta.comment] = extract_first_instance_from_field_metadata(info, pg_table_meta.comment)
            col_data['comment'] = comment
            columns.append(col_data)
        if len(columns) <= 0:
            raise FlowComponentException(self.name, [f'Class {target} must declare columns.'])
        accumulator.add_definition('columns', columns)


class TableExtractCheckConstraintsComponent(CommonExtractCheckConstraintsComponent,
                                            TableDependsOnValidationComponents):
    pass


class TableStoreExtractedPrimaryKeyComponent(FlowComponent):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('store-extracted-primary-key-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('primary_key', 'extraction')

        pk: pg_primary_key_definition = None if definition is None else pg_primary_key_definition(**(definition[0] | {
            'column_name': tuple(definition[0]['column_name'])}))

        @classmethod
        def __pg_primary_key(cls) -> Optional[pg_primary_key_definition]:
            return pk

        accumulator.add_definition('__pg_primary_key', __pg_primary_key)

    def get_dependencies(self) -> tuple[str]:
        return ('extract-primary-key-definition-from-declaration-component', )


class TableStoreExtractedIndexComponent(FlowComponent):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('store-extracted-index-component')

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
        return ('extract-unique-index-definition-from-declaration-component',
                'extract-index-definition-from-declaration-component')


class TableStoreCheckConstraintsComponent(CommonStoreCheckConstraintsComponent):
    def get_dependencies(self) -> tuple[str]:
        return ('extract-check-constraints-component', )


class TableStoreExtractedForeignKeyComponent(FlowComponent):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('store-extracted-foreign-key-component')

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
        return ('extract-foreign-key-definition-from-declaration-component', )


class TableStoreExtractedInheritedClassesComponent(FlowComponent):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('store-extracted-inherited-classes-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        base_classes: tuple[type[Any]] = accumulator.get_definition('inherited', 'extraction')

        @classmethod
        def __pg_base_classes(cls) -> tuple[type[Any]]:
            return tuple() if base_classes is None else base_classes

        accumulator.add_definition('__pg_base_classes', __pg_base_classes)

    def get_dependencies(self) -> tuple[str]:
        return ('extract-inheritance-definition-from-declaration-component', )


class TableStoreExtractedColumnsComponent(FlowComponent):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('store-columns-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('columns', 'extraction')
        columns: list[pg_column_definition] = [pg_column_definition(**col) for col in definition]

        @classmethod
        def __pg_columns(cls) -> list[pg_column_definition]:
            return columns

        accumulator.add_definition('__pg_columns', __pg_columns)

    def get_dependencies(self) -> tuple[str]:
        return ('extract-column-definition-from-declaration-component', )


class TableStoreFinalDefinitionComponent(FlowComponent):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('store-final-definition-component')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Any] = accumulator.get_definition('built')
        accumulator.add_definition('final', {} if definition is None else definition)

    def get_dependencies(self) -> tuple[str]:
        return ('store-columns-component', )


with pg_table_definition_flow.at_work_path('validation') as flow:
    flow.register(TableValidateExistingColumnsComponent())
    flow.register(TableValidateConsistentBaseClassesComponent())
    flow.register(TableValidateRestrictedMetadataTypesComponent([
        pg_table_meta.foreign_key,
        pg_table_meta.primary_key,
        pg_table_meta.index,
        pg_table_meta.unique_index,
        pg_table_meta.check,
        pg_table_meta.default.value,
        pg_table_meta.default.nextval,
        pg_table_meta.comment]))
    flow.register(TableValidateUniqueMetadataTypesComponent([
        pg_table_meta.foreign_key,
        pg_table_meta.primary_key,
        pg_table_meta.default.value,
        pg_table_meta.default.nextval,
        pg_table_meta.comment,
        pg_table_meta.check]))
    flow.register(TableValidateFieldsBaseTypeComponent(
        type_subclass=[
            pg_enum,
            pg_composite],
        type_instance=[
            pg_builtin,
            pg_domain]))

with pg_table_definition_flow.at_work_path('merge') as flow:
    flow.register(TableMergeInheritedFieldsComponent().critical())

with pg_table_definition_flow.at_work_path('extraction') as flow:
    flow.register(TableExtractIndexDefinitionFromDeclarationComponent().critical())
    flow.register(TableExtractCheckConstraintsComponent())
    flow.register(TableExtractPrimaryKeyDefinitionFromDeclarationComponent())
    flow.register(TableExtractForeignKeyDefinitionFromDeclarationComponent())
    flow.register(TableExtractUniqueIndexDefinitionFromDeclarationComponent())
    flow.register(TableExtractInheritanceDefinitionFromDeclarationComponent())
    flow.register(TableExtractColumnDefinitionFromDeclarationComponent())

with pg_table_definition_flow.at_work_path('built') as flow:
    flow.register(TableStoreExtractedPrimaryKeyComponent().critical())
    flow.register(TableStoreExtractedIndexComponent())
    flow.register(TableStoreExtractedForeignKeyComponent())
    flow.register(TableStoreExtractedInheritedClassesComponent())
    flow.register(TableStoreExtractedColumnsComponent())
    flow.register(TableStoreCheckConstraintsComponent())

with pg_table_definition_flow.at_work_path('') as flow:
    flow.register(TableStoreFinalDefinitionComponent())


__all__ = {
    'pg_table': pg_table,
    'pg_table_meta': pg_table_meta}
