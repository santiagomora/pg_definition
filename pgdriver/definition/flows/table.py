from typing import\
    Optional
from pgdriver.definition.flows import\
    FlowComponent,\
    FlowAccumulator,\
    TypeSubclassDefinitionFlow,\
    FlowComponentException
from pgdriver.definition.common import\
    CommonValidateRestrictedMetadataTypesComponent,\
    CommonValidateUniqueMetadataTypesComponent,\
    CommonValidateFieldsBaseTypeComponent,\
    CommonExtractCheckConstraintsComponent,\
    CommonStoreCheckConstraintsComponent
from pgdriver.definition.tools.metadata import\
    pg_foreign_key_meta,\
    pg_primary_key_meta,\
    pg_index_meta,\
    pg_unique_index_meta,\
    pg_check_meta,\
    pg_comment_meta
from typing import\
    Any
from pgdriver.definition.inspection import\
    extract_by_instance_type_from_model_fields_info,\
    aggregate,\
    ordered_set_accumulator,\
    key_by,\
    extract_by_instance_type_from_inherited_classes,\
    extract_first_instance_from_field_metadata
from pydantic.fields import\
    FieldInfo
import deepdiff
from ordered_set import\
    OrderedSet
from pgdriver.definition.build import\
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
    We must ensure that target definition inherits from classes
    with the same base class
    """

    def __init__(self):
        super().__init__('validate-consistent-base-classes-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        for base_class in extract_by_instance_type_from_inherited_classes(target, pg_table):
            if not issubclass(base_class, pg_table):
                errors.append(f'Inherited class {base_class} must be a subclass of {pg_table.__name__}')
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)

    def get_dependencies(self) -> tuple[str]:
        return tuple()


class TableValidateRestrictedMetadataTypesComponent(CommonValidateRestrictedMetadataTypesComponent[pg_table]):
    def get_dependencies(self) -> tuple[str]:
        return tuple()


class TableValidateUniqueMetadataTypesComponent(CommonValidateUniqueMetadataTypesComponent[pg_table]):
    def get_dependencies(self) -> tuple[str]:
        return tuple()


class TableValidateFieldsBaseTypeComponent(CommonValidateFieldsBaseTypeComponent[pg_table]):
    def get_dependencies(self) -> tuple[str]:
        return tuple()


class TableValidateInheritedFieldsComponent(FlowComponent[pg_table]):
    """
    We must be sure that class attributes wont change inherited attributes
    """

    def __init__(self):
        super().__init__('validate-inherited-fields-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        for base_class in extract_by_instance_type_from_inherited_classes(target, pg_table):
            for class_attr in base_class.model_fields:
                if class_attr in target.model_fields:
                    if deepdiff.DeepDiff(base_class.model_fields[class_attr], target.model_fields[class_attr], ignore_order=True) != {}:
                        # tengo que indicar el atributo compartido que esta fallando
                        # en realidad me voy por el camino facil porque si yo sobreescribo
                        # un atributo podria fortalecer el check y aun asi satisfacer la condicion de la clase base por liskov
                        errors.append(f'Inherited attribute {class_attr} must have same definition in base class {base_class.__name__}')
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)

    def get_dependencies(self) -> tuple[str]:
        return tuple()


class TableValidateConsistentForeignKeysComponent(FlowComponent[pg_table]):
    """
    We must ensure that columns pointed by foreign keys share type
    with columns in base class
    """

    def __init__(self):
        super().__init__()

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        for base_class in extract_by_instance_type_from_inherited_classes(target, pg_table):
            if not issubclass(base_class, pg_table):
                errors.append(f'Inherited class {base_class} must be a subclass of {pg_target.__name__}')
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)

    def get_dependencies(self) -> tuple[str]:
        return tuple()


class TableExtractIndexDefinitionFromDeclarationComponent(FlowComponent[pg_table]):
    """
    Table index can be set via decorators or inferred from field metadata
    """

    def __init__(self):
        super().__init__('extract-index-definition-from-declaration-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        if hasattr('__pg_get_indexes'):
            return
        indexes: list[dict[str, Any]] = extract_by_instance_type_from_model_fields_info(
            target.model_fields,
            pg_index_meta,
            lambda field_name, index: {
                'ix_column': field_name,
                'ix_type':   index.type,
                'ix_name':   index.name})
        try:
            grouped_by_name: dict[str, list[dict[str, Any]]] = key_by(
                ('ix_name', ),
                indexes)
            definition: list[dict[str, Any]] = [aggregate(grouped_by_name[ix_name], {
                    'ix_column': ordered_set_accumulator}) for ix_name in grouped_by_name]
            if len(definition) > 0:
                accumulator.add_definition('indexes', definition)
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])

    def get_dependencies(self) -> tuple[str]:
        return tuple('validate-consistent-base-classes-component',
                     'validate-restricted-metadata-types-component',
                     'validate-unique-metadata-types-component',
                     'validate-fields-base-type-component',
                     'validate-inherited-fields-component')


class TableExtractPrimaryKeyDefinitionFromDeclarationComponent(FlowComponent[pg_table]):
    # un campo solo puede tener una declaracion de builtin
    def __init__(self):
        super().__init__('extract-primary-key-definition-from-declaration-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        pks: list[dict[str, Any]] = extract_by_instance_type_from_model_fields_info(
            target.model_fields,
            pg_primary_key_meta,
            lambda field_name, pk: {
                'pk_column': field_name,
                'pk_name':   pk.name})
        try:
            grouped_by_name: dict[str, list[dict[str, Any]]] = key_by(
                ('pk_name', ),
                pks)
            definition: list[dict[str, Any]] = [aggregate(grouped_by_name[pk_name], {
                    'pk_column': ordered_set_accumulator}) for pk_name in grouped_by_name]
            if len(definition) > 0:
                accumulator.add_definition('primary_keys', definition)
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])

    def get_dependencies(self) -> tuple[str]:
        return tuple('validate-consistent-base-classes-component',
                     'validate-restricted-metadata-types-component',
                     'validate-unique-metadata-types-component',
                     'validate-fields-base-type-component',
                     'validate-inherited-fields-component')


class TableExtractForeignKeyDefinitionFromDeclarationComponent(FlowComponent[pg_table]):
    # un campo solo puede tener una declaracion de builtin
    def __init__(self):
        super().__init__('extract-foreign-key-definition-from-declaration-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        fks: list[dict[str, Any]] = extract_by_instance_type_from_model_fields_info(
            target.model_fields,
            pg_foreign_key_meta,
            lambda field_name, fk: {
                'fk_name':                    fk.name,
                'fk_other_class':             fk.other_class,
                'fk_other_class_column_name': fk.other_class_column_name,
                'fk_on_update':               fk.on_update,
                'fk_on_delete':               fk.on_delete,
                'fk_column':                  field_name})
        try:
            grouped_by_name: dict[str, list[dict[str, Any]]] = key_by(
                ('fk_name', ),
                fks)
            definition: list[dict[str, Any]] = [aggregate(grouped_by_name[fk_name], {
                    'fk_column': ordered_set_accumulator,
                    'fk_other_class_column_name': ordered_set_accumulator}) for fk_name in grouped_by_name]
            if len(definition) > 0:
                accumulator.add_definition('foreign_keys', definition)
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])

    def get_dependencies(self) -> tuple[str]:
        return tuple('validate-consistent-base-classes-component',
                     'validate-restricted-metadata-types-component',
                     'validate-unique-metadata-types-component',
                     'validate-fields-base-type-component',
                     'validate-inherited-fields-component')


class TableExtractUniqueIndexDefinitionFromDeclarationComponent(FlowComponent[pg_table]):
    # un campo solo puede tener una declaracion de builtin
    def __init__(self):
        super().__init__('extract-unique-index-definition-from-declaration-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        uixs: list[dict[str, Any]] = extract_by_instance_type_from_model_fields_info(
            target.model_fields,
            pg_unique_index_meta,
            lambda field_name, uix: {
                'uix_column': field_name,
                'uix_name':   uix.name})
        try:
            grouped_by_name: dict[str, list[dict[str, Any]]] = key_by(
                ('uix_name', ),
                uixs)
            definition: list[dict[str, Any]] = [aggregate(grouped_by_name[uix_name], {
                    'uix_column': ordered_set_accumulator}) for uix_name in grouped_by_name]
            if len(definition) > 0:
                accumulator.add_definition('unique_indexes', definition)
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])

    def get_dependencies(self) -> tuple[str]:
        return tuple('validate-consistent-base-classes-component',
                     'validate-restricted-metadata-types-component',
                     'validate-unique-metadata-types-component',
                     'validate-fields-base-type-component',
                     'validate-inherited-fields-component')


class TableExtractInheritanceDefinitionFromDeclarationComponent(FlowComponent[pg_table]):
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

    def get_dependencies(self) -> tuple[str]:
        return tuple('validate-consistent-base-classes-component',
                     'validate-restricted-metadata-types-component',
                     'validate-unique-metadata-types-component',
                     'validate-fields-base-type-component',
                     'validate-inherited-fields-component')


class TableExtractColumnDefinitionFromDeclarationComponent(FlowComponent[pg_table]):
    def __init__(self):
        super().__init__('extract-column-definition-from-declaration-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        # extraer las definiciones de columna
        columns: list[dict[str, Any]] = []
        for name, info in target.model_fields.items():
            check: Optional[pg_check_meta] = extract_first_instance_from_field_metadata(info, pg_check_meta)
            col_data: dict[str, Any] = {
                'col_name': name,
                'col_type': info.annotation}
            if check is not None:
                col_data['col_check'] = check
            comment: Optional[pg_comment_meta] = extract_first_instance_from_field_metadata(info, pg_comment_meta)
            if comment is not None:
                col_data['col_comment'] = comment
            columns.append(col_data)
        if len(columns) > 0:
            accumulator.add_definition('columns', columns)
        raise FlowComponentException(self.name, f'Class {target.__name__} must declare columns.')

    def get_dependencies(self) -> tuple[str]:
        return tuple('validate-consistent-base-classes-component',
                     'validate-restricted-metadata-types-component',
                     'validate-unique-metadata-types-component',
                     'validate-fields-base-type-component',
                     'validate-inherited-fields-component')


class TableExtractCheckConstraintsComponent(CommonExtractCheckConstraintsComponent[pg_table]):
    def get_dependencies(self) -> tuple[str]:
        return tuple('validate-consistent-base-classes-component',
                     'validate-restricted-metadata-types-component',
                     'validate-unique-metadata-types-component',
                     'validate-fields-base-type-component',
                     'validate-inherited-fields-component')


class TableValidateExtractedForeignKeyDefinitionComponent(FlowComponent[pg_table]):
    """
    Validates that extracted foreign keys columns are columns of the
    same type in the other class
    """

    def __init__(self):
        super().__init__('validate-extracted-foreign-key-definition-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('foreign_keys', 'extraction')
        fks: list[dict[str, Any]] = [] if definition is None else definition
        fields: dict[str, FieldInfo] = target.model_fields
        errors: list[str] = []
        for fk_definition in fks:
            other_fields: dict[str, FieldInfo] = fk_definition['fk_other_class'].model_fields
            other_class_name: str = fk_definition['fk_other_class'].__name__
            fk_name: str = fk_definition['fk_name']
            for ix, other_column_name in enumerate(fk_definition['fk_other_class_column_name']):
                iter_errors: list[str] = []
                if other_column_name not in other_fields:
                    iter_errors.append(f'{fk_name}: Foreign key column {other_column_name} doesnt exist in class {other_class_name}')
                    continue
                column: type = fields[fk_definition['fk_column'][ix]].annotation
                if other_fields[other_column_name].annotation != column:
                    iter_errors.append(f'{fk_name}: Foreign key column {other_column_name} must be of type {column.__name__}')
                errors += iter_errors
        if len(errors) != 0:
            raise FlowComponentException(self.name, errors)

    def get_dependencies(self) -> tuple[str]:
        return tuple('extract-foreign-key-definition-from-declaration-component')


class TableValidateExtractedUniqueIndexDefinitionComponent(FlowComponent[pg_table]):
    """
    Validates that a column doesnt appear in more than one unique index definition
    """

    def __init__(self):
        super().__init__('validate-extracted-unique-index-definition-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('unique_indexes', 'extraction')
        uixs: list[dict[str, Any]] = [] if definition is None else definition 
        columns: Optional[OrderedSet[str]] = None
        for uix_definition in uixs:
            if columns is None:
                columns = uix_definition['uix_column']
            else:
                if columns.intersection(uix_definition['uix_column']).count() > 0:
                    message: str = 'Column appears in more than one unique index definition'
                    raise FlowComponentException(self.name, [message])

    def get_dependencies(self) -> tuple[str]:
        return tuple('extract-unique-index-definition-from-declaration-component')


class TableValidateExtractedPrimaryKeyDefinitionComponent(FlowComponent[pg_table]):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('validate-extracted-primary-key-definition-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('primary_keys', 'extraction')
        pks: list[dict[str, Any]] = [] if definition is None else definition
        columns: Optional[OrderedSet[str]] = None
        for pk_definition in pks:
            if columns is None:
                columns = pk_definition['pk_column']
            else:
                if columns.intersection(pk_definition['pk_column']).count() > 0:
                    raise FlowComponentException(self.name, ['Column appears in more than one primary key definition'])

    def get_dependencies(self) -> tuple[str]:
        return tuple('extract-primary-key-definition-from-declaration-component')


class TableStoreExtractedPrimaryKeyComponent(FlowComponent[pg_table]):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('store-extracted-primary-key-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('primary_keys', 'extraction')
        if definition is None:
            return

        pks: list[pg_primary_key] = [pg_primary_key(**(pk | {
            'pk_column': tuple(pk['pk_column'])})) for pk in definition]

        @classmethod
        def __pg_get_primary_key(cls) -> list[pg_primary_key]:
            return pks

        accumulator.add_definition('__pg_get_primary_key', __pg_get_primary_key)

    def get_dependencies(self) -> tuple[str]:
        return tuple('validate-extracted-primary-key-definition-component')


class TableStoreExtractedUniqueIndexComponent(FlowComponent[pg_table]):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('store-extracted-primary-key-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('unique_indexes', 'extraction')
        if definition is None:
            return

        uixs: list[pg_unique_index] = [pg_unique_index(**(uix | {
            'uix_column': tuple(uix['uix_column'])})) for uix in definition]

        @classmethod
        def __pg_get_unique_indexes(cls) -> list[pg_unique_index]:
            return uixs

        accumulator.add_definition('__pg_get_unique_indexes', __pg_get_unique_indexes)

    def get_dependencies(self) -> tuple[str]:
        return tuple('validate-extracted-unique-index-definition-component')


class TableStoreCheckConstraintsComponent(CommonStoreCheckConstraintsComponent[pg_table]):
    def get_dependencies(self) -> tuple[str]:
        return tuple('extract-check-constraints-component')


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
            'ix_column': tuple(ix['ix_column'])})) for ix in definition]

        @classmethod
        def __pg_get_indexes(cls) -> list[pg_index]:
            return ixs

        accumulator.add_definition('__pg_get_indexes', __pg_get_indexes)

    def get_dependencies(self) -> tuple[str]:
        return tuple('extract-index-definition-from-declaration-component')


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
            'fk_column': tuple(fk['fk_column']),
            'fk_other_class_column_name': tuple(fk['fk_other_class_column_name'])})) for fk in definition]

        @classmethod
        def __pg_get_foreign_keys(cls) -> list[pg_foreign_key]:
            return fks

        accumulator.add_definition('__pg_get_foreign_keys', __pg_get_foreign_keys)

    def get_dependencies(self) -> tuple[str]:
        return tuple('validate-extracted-unique-index-definition-component')


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
        def __pg_get_base_classes(cls) -> tuple[type[Any]]:
            return base_classes

        accumulator.add_definition('__pg_get_base_classes', __pg_get_base_classes)

    def get_dependencies(self) -> tuple[str]:
        return tuple('extract-inheritance-definition-from-declaration-component')


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
        def __pg_get_columns(cls) -> list[pg_column]:
            return columns

        accumulator.add_definition('__pg_get_columns', __pg_get_columns)

    def get_dependencies(self) -> tuple[str]:
        return tuple('extract-column-definition-from-declaration-component')


class TableDefinitionFlow(TypeSubclassDefinitionFlow[pg_table]):
    def __init__(self):
        super().__init__('pgdriver-table-definition-flow')


pgtable_definition_flow: TableDefinitionFlow = TableDefinitionFlow()

with pgtable_definition_flow.at_path('validation') as flow:
    flow.register_component(
        TableValidateConsistentBaseClassesComponent())
    flow.register_component(
        TableValidateInheritedFieldsComponent())
    flow.register_component(
        TableValidateRestrictedMetadataTypesComponent())
    flow.register_component(
        TableValidateRestrictedMetadataTypesComponent([
            pg_foreign_key_meta,
            pg_primary_key_meta,
            pg_index_meta,
            pg_unique_index_meta,
            pg_check_meta,
            pg_comment_meta]))
    flow.register_component(
        TableValidateUniqueMetadataTypesComponent([
            pg_foreign_key_meta,
            pg_primary_key_meta,
            pg_unique_index_meta,
            pg_comment_meta,
            pg_check_meta]))
    flow.register_component(
        TableValidateFieldsBaseTypeComponent([
            pg_enum,
            pg_composite], [
            pg_builtin,
            pg_domain]))
    flow.register_component(
        TableValidateConsistentForeignKeysComponent())

with pgtable_definition_flow.at_path('extraction') as flow:
    flow.register(TableExtractIndexDefinitionFromDeclarationComponent().critical())
    flow.register(TableExtractCheckConstraintsComponent())
    flow.register(TableExtractPrimaryKeyDefinitionFromDeclarationComponent())
    flow.register(TableExtractForeignKeyDefinitionFromDeclarationComponent())
    flow.register(TableExtractUniqueIndexDefinitionFromDeclarationComponent())
    flow.register(TableExtractInheritanceDefinitionFromDeclarationComponent())
    flow.register(TableExtractColumnDefinitionFromDeclarationComponent())

    # work at extraction.validation path
    with pgtable_definition_flow.at_path('validation') as flow:
        flow.register(TableValidateExtractedForeignKeyDefinitionComponent().critical())
        flow.register(TableValidateExtractedUniqueIndexDefinitionComponent())
        flow.register(TableValidateExtractedPrimaryKeyDefinitionComponent())

with pgtable_definition_flow.at_path('final') as flow:
    flow.register(TableStoreExtractedPrimaryKeyComponent().critical())
    flow.register(TableStoreExtractedUniqueIndexComponent())
    flow.register(TableStoreExtractedIndexComponent())
    flow.register(TableStoreExtractedForeignKeyComponent())
    flow.register(TableStoreExtractedInheritedClassesComponent())
    flow.register(TableStoreExtractedColumnsComponent())
    flow.register(TableStoreCheckConstraintsComponent())


__all__ = {'pgtable_definition_flow': pgtable_definition_flow}
