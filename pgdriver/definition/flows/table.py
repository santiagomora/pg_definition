from typing import\
    Optional
from pgdriver.definition.flows import\
    FlowComponent,\
    FlowAccumulator,\
    TypeSubclassDefinitionFlow,\
    FlowComponentException
from pgdriver.definition.flows.common import\
    CommonValidateRestrictedMetadataTypesComponent,\
    CommonValidateUniqueMetadataTypesComponent,\
    CommonValidateFieldsBaseTypeComponent,\
    CommonExtractCheckConstraintsComponent,\
    CommonStoreCheckConstraintsComponent,\
    ValidatesConflictingDefinitions
from pgdriver.definition.build import\
    pg_meta,\
    pg_table,\
    pg_primary_key,\
    pg_unique_index,\
    pg_foreign_key,\
    pg_index,\
    pg_column,\
    pg_domain,\
    pg_composite,\
    pg_enum,\
    pg_builtin
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
class TableValidateConsistentBaseClassesComponent(FlowComponent[pg_table]):
    """
    We must ensure that target definition inherits from classes with the same 
    base class. Also we must validate that base classes columns/fields wont
    collide between them.
    """

    def __init__(self):
        super().__init__('validate-consistent-base-classes-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
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


class TableValidateExistingColumnsComponent(FlowComponent[pg_table]):
    """
    We must ensure that target definition has fields
    """

    def __init__(self):
        super().__init__('validate-existing-columns-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        if len(target.model_fields.keys()) <= 0:
            raise FlowComponentException(self.name, [f'Class {target} must define columns.'])


class TableValidateRestrictedMetadataTypesComponent(CommonValidateRestrictedMetadataTypesComponent[pg_table]):
    pass


class TableValidateUniqueMetadataTypesComponent(CommonValidateUniqueMetadataTypesComponent[pg_table]):
    pass


class TableValidateFieldsBaseTypeComponent(CommonValidateFieldsBaseTypeComponent[pg_table]):
    pass


class TableMergeInheritedFieldsComponent(FlowComponent[pg_table]):
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

    def _merge_from_parents(self, target: type[pg_table], overwritten_fields: dict[str, list[Any]], meta_type: type) -> None:
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

    def _inherit_from_parents(self, target: type[pg_table], overwritten_fields: dict[str, list[Any]], meta_type: type) -> None:
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

    def _validate_consistent_inherited_metadata(self, target: type[pg_table], overwritten_fields: dict[str, list[Any]], meta_type: type) -> list[str]:
        # Extract default values and validate all equal
        errors: list[str] = []
        for name in overwritten_fields:
            initial: Optional[Any] = extract_first_instance_from_field_metadata(target.model_fields[name], meta_type)
            inherited_meta: list[Any] = extract_by_instance_type_from_list(overwritten_fields[name], meta_type)
            if not meta_type.consistent_list([initial] + inherited_meta if initial is not None else inherited_meta):
                errors.append(f'Inconsistencies detected in inherited field {name} metadata {meta_type}')
        return errors

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
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
        errors += self._validate_consistent_inherited_metadata(target, overwritten_fields, pg_meta.default.value)
        errors += self._validate_consistent_inherited_metadata(target, overwritten_fields, pg_meta.default.nextval)
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)
        self._merge_from_parents(target, overwritten_fields, pg_meta.check)
        self._inherit_from_parents(target, overwritten_fields, pg_meta.default.value)
        self._inherit_from_parents(target, overwritten_fields, pg_meta.default.nextval)
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


class TableExtractIndexDefinitionFromDeclarationComponent(FlowComponent[pg_table],
                                                          ValidatesConflictingDefinitions,
                                                          TableDependsOnValidationComponents):
    """
    Table index can be set via decorators or inferred from field metadata
    """

    def __init__(self):
        super().__init__('extract-index-definition-from-declaration-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        indexes: list[dict[str, Any]] = [ix for ix in extract_by_instance_type_from_model_fields_info(
            target,
            pg_meta.index,
            self._base_class,
            lambda field_name, index: {
                'ix_column_name': field_name,
                'ix_type':   index.type,
                'ix_name':   index.name})]
        try:
            grouped_by_name: dict[str, list[dict[str, Any]]] = key_by(
                ('ix_name', ),
                indexes)
            definition: list[dict[str, Any]] = [aggregate(grouped_by_name[ix_name], {
                    'ix_column_name': ordered_set_accumulator}) for ix_name in grouped_by_name]
            if len(definition) <= 0:
                return
            self.check_conflicting_definitions(target, 'indexes')
            accumulator.add_definition('indexes', definition)
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])


class TableExtractPrimaryKeyDefinitionFromDeclarationComponent(FlowComponent[pg_table],
                                                               ValidatesConflictingDefinitions,
                                                               TableDependsOnValidationComponents):
    # un campo solo puede tener una declaracion de builtin
    def __init__(self):
        super().__init__('extract-primary-key-definition-from-declaration-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        pks: list[dict[str, Any]] = [pk for pk in extract_by_instance_type_from_model_fields_info(
            target,
            pg_meta.primary_key,
            self._base_class,
            lambda field_name, pk: {
                'pk_column_name': field_name,
                'pk_name':   pk.name})]
        try:
            grouped_by_name: dict[str, list[dict[str, Any]]] = key_by(
                ('pk_name', ),
                pks)
            definition: list[dict[str, Any]] = [aggregate(grouped_by_name[pk_name], {
                    'pk_column_name': ordered_set_accumulator}) for pk_name in grouped_by_name]
            if len(definition) <= 0:
                return
            self.check_conflicting_definitions(target, 'primary_key')
            accumulator.add_definition('primary_key', definition)
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])


class TableExtractForeignKeyDefinitionFromDeclarationComponent(FlowComponent[pg_table],
                                                               ValidatesConflictingDefinitions,
                                                               TableDependsOnValidationComponents):
    # un campo solo puede tener una declaracion de builtin
    def __init__(self):
        super().__init__('extract-foreign-key-definition-from-declaration-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        fks: list[dict[str, Any]] = [fk for fk in extract_by_instance_type_from_model_fields_info(
            target,
            pg_meta.foreign_key,
            self._base_class,
            lambda field_name, fk: {
                'fk_name':                    fk.name,
                'fk_other_class':             fk.other_class,
                'fk_other_class_column_name': fk.other_class_column_name,
                'fk_on_update':               fk.on_update,
                'fk_on_delete':               fk.on_delete,
                'fk_class_column_name':       field_name})]
        try:
            grouped_by_name: dict[str, list[dict[str, Any]]] = key_by(
                ('fk_name', ),
                fks)
            definition: list[dict[str, Any]] = [aggregate(grouped_by_name[fk_name], {
                    'fk_class_column_name': ordered_set_accumulator,
                    'fk_other_class_column_name': ordered_set_accumulator}) for fk_name in grouped_by_name]
            if len(definition) <= 0:
                return
            self.check_conflicting_definitions(target, 'foreign_keys')
            accumulator.add_definition('foreign_keys', definition)
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])


class TableExtractUniqueIndexDefinitionFromDeclarationComponent(FlowComponent[pg_table],
                                                                ValidatesConflictingDefinitions,
                                                                TableDependsOnValidationComponents):
    # un campo solo puede tener una declaracion de builtin
    def __init__(self):
        super().__init__('extract-unique-index-definition-from-declaration-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        uixs: list[dict[str, Any]] = [uix for uix in extract_by_instance_type_from_model_fields_info(
            target,
            pg_meta.unique_index,
            self._base_class,
            lambda field_name, uix: {
                'uix_column_name': field_name,
                'uix_name':   uix.name})]
        try:
            grouped_by_name: dict[str, list[dict[str, Any]]] = key_by(
                ('uix_name', ),
                uixs)
            definition: list[dict[str, Any]] = [aggregate(grouped_by_name[uix_name], {
                    'uix_column_name': ordered_set_accumulator}) for uix_name in grouped_by_name]
            if len(definition) <= 0:
                return
            self.check_conflicting_definitions(target, 'unique_indexes')
            accumulator.add_definition('unique_indexes', definition)
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])


class TableExtractInheritanceDefinitionFromDeclarationComponent(FlowComponent[pg_table],
                                                                TableDependsOnValidationComponents):
    # un campo solo puede tener una declaracion de builtin
    def __init__(self):
        super().__init__('extract-inheritance-definition-from-declaration-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        try:
            inherited: list[type] = extract_by_instance_type_from_inherited_classes(
                target,
                pg_table)
            if len(inherited) > 0:
                accumulator.add_definition('inherited', inherited)
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])


class TableExtractColumnDefinitionFromDeclarationComponent(FlowComponent[pg_table],
                                                           TableDependsOnValidationComponents):
    def __init__(self):
        super().__init__('extract-column-definition-from-declaration-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        # extraer las definiciones de columna
        columns: list[dict[str, Any]] = []
        for name, info in target.model_fields.items():
            check: Optional[pg_meta.check] = extract_first_instance_from_field_metadata(info, pg_meta.check)
            col_data: dict[str, Any] = {
                'col_name': name,
                'col_type': info.annotation}
            if check is not None:
                col_data['col_check'] = check
            comment: Optional[pg_meta.comment] = extract_first_instance_from_field_metadata(info, pg_meta.comment)
            if comment is not None:
                col_data['col_comment'] = comment
            columns.append(col_data)
        if len(columns) <= 0:
            raise FlowComponentException(self.name, [f'Class {target} must declare columns.'])
        accumulator.add_definition('columns', columns)


class TableExtractCheckConstraintsComponent(CommonExtractCheckConstraintsComponent[pg_table],
                                            TableDependsOnValidationComponents):
    pass


class TableStoreExtractedPrimaryKeyComponent(FlowComponent[pg_table]):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('store-extracted-primary-key-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('primary_key', 'extraction')
        if definition is None:
            return

        pk: pg_primary_key = pg_primary_key(**(definition[0] | {
            'pk_column_name': tuple(definition[0]['pk_column_name'])}))

        @classmethod
        def __pg_primary_key(cls) -> list[pg_primary_key]:
            return pk

        accumulator.add_definition('__pg_primary_key', __pg_primary_key)

    def get_dependencies(self) -> tuple[str]:
        return ('extract-primary-key-definition-from-declaration-component', )


class TableStoreExtractedUniqueIndexComponent(FlowComponent[pg_table]):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('store-extracted-unique-index-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('unique_indexes', 'extraction')
        if definition is None:
            return

        uixs: list[pg_unique_index] = [pg_unique_index(**(uix | {
            'uix_column_name': tuple(uix['uix_column_name'])})) for uix in definition]

        @classmethod
        def __pg_unique_indexes(cls) -> list[pg_unique_index]:
            return uixs

        accumulator.add_definition('__pg_unique_indexes', __pg_unique_indexes)

    def get_dependencies(self) -> tuple[str]:
        return ('extract-unique-index-definition-from-declaration-component', )


class TableStoreCheckConstraintsComponent(CommonStoreCheckConstraintsComponent[pg_table]):
    def get_dependencies(self) -> tuple[str]:
        return ('extract-check-constraints-component', )


class TableStoreExtractedIndexComponent(FlowComponent[pg_table]):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('store-extracted-index-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('indexes', 'extraction')
        if definition is None:
            return

        ixs: list[pg_index] = [pg_index(**(ix | {
            'ix_column_name': tuple(ix['ix_column_name'])})) for ix in definition]

        @classmethod
        def __pg_indexes(cls) -> list[pg_index]:
            return ixs

        accumulator.add_definition('__pg_indexes', __pg_indexes)

    def get_dependencies(self) -> tuple[str]:
        return ('extract-index-definition-from-declaration-component', )


class TableStoreExtractedForeignKeyComponent(FlowComponent[pg_table]):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('store-extracted-foreign-key-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('foreign_keys', 'extraction')
        if definition is None:
            return

        fks: list[pg_foreign_key] = [pg_foreign_key(**(fk | {
            'fk_class_column_name': tuple(fk['fk_class_column_name']),
            'fk_other_class_column_name': tuple(fk['fk_other_class_column_name'])})) for fk in definition]

        @classmethod
        def __pg_foreign_keys(cls) -> list[pg_foreign_key]:
            return fks

        accumulator.add_definition('__pg_foreign_keys', __pg_foreign_keys)

    def get_dependencies(self) -> tuple[str]:
        return ('extract-foreign-key-definition-from-declaration-component', )


class TableStoreExtractedInheritedClassesComponent(FlowComponent[pg_table]):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('store-extracted-inherited-classes-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        definition: tuple[type[Any]] = accumulator.get_definition('inherited', 'extraction')
        if definition is None:
            return
        base_classes: tuple[type[Any]] = definition

        @classmethod
        def __pg_base_classes(cls) -> tuple[type[Any]]:
            return base_classes

        accumulator.add_definition('__pg_base_classes', __pg_base_classes)

    def get_dependencies(self) -> tuple[str]:
        return ('extract-inheritance-definition-from-declaration-component', )


class TableStoreExtractedColumnsComponent(FlowComponent[pg_table]):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('store-columns-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('columns', 'extraction')
        if definition is None:
            return
        columns: list[pg_column] = [pg_column(**col) for col in definition]

        @classmethod
        def __pg_columns(cls) -> list[pg_column]:
            return columns

        accumulator.add_definition('__pg_columns', __pg_columns)

    def get_dependencies(self) -> tuple[str]:
        return ('extract-column-definition-from-declaration-component', )


class TableDefinitionFlow(TypeSubclassDefinitionFlow[pg_table]):
    def __init__(self):
        super().__init__('pgdriver-table-definition-flow')


pg_table_definition_flow: TableDefinitionFlow = TableDefinitionFlow()

with pg_table_definition_flow.at_work_path('validation') as flow:
    flow.register(TableValidateExistingColumnsComponent())
    flow.register(TableValidateConsistentBaseClassesComponent())
    flow.register(TableValidateRestrictedMetadataTypesComponent([
        pg_meta.foreign_key,
        pg_meta.primary_key,
        pg_meta.index,
        pg_meta.unique_index,
        pg_meta.check,
        pg_meta.default.value,
        pg_meta.default.nextval,
        pg_meta.comment]))
    flow.register(TableValidateUniqueMetadataTypesComponent([
        pg_meta.foreign_key,
        pg_meta.primary_key,
        pg_meta.default.value,
        pg_meta.default.nextval,
        pg_meta.comment,
        pg_meta.check]))
    flow.register(TableValidateFieldsBaseTypeComponent(type_subclass=[
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

with pg_table_definition_flow.at_work_path('final') as flow:
    flow.register(TableStoreExtractedPrimaryKeyComponent().critical())
    flow.register(TableStoreExtractedUniqueIndexComponent())
    flow.register(TableStoreExtractedIndexComponent())
    flow.register(TableStoreExtractedForeignKeyComponent())
    flow.register(TableStoreExtractedInheritedClassesComponent())
    flow.register(TableStoreExtractedColumnsComponent())
    flow.register(TableStoreCheckConstraintsComponent())


__all__ = {'pg_table_definition_flow': pg_table_definition_flow}
