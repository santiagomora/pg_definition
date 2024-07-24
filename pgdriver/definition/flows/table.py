from typing import\
    Optional
from pgdriver.definition.flows import\
    FlowComponent,\
    FlowAccumulator,\
    FlowComponentException,\
    T
from pgdriver.definition.tools.metadata import\
    pg_foreign_key_meta,\
    pg_primary_key_meta,\
    pg_index_meta,\
    pg_unique_index_meta,\
    pg_check_meta,\
    pg_comment_meta
from pgdriver.definition.types.builtin import\
    pg_builtin
from typing import\
    Any
from pgdriver.definition.tools.inspection import\
    extract_by_instance_type_from_model_fields_info,\
    aggregate,\
    ordered_set_accumulator,\
    key_by,\
    get_field_classified_metadata_appearances,\
    extract_by_instance_type_from_inherited_classes,\
    extract_first_instance_from_field_metadata
from pydantic.fields import\
    FieldInfo
import deepdiff
from ordered_set import\
    OrderedSet
from pgdriver.definition.tools import\
    pg_table


# una tabla puede heredar unicamente de otra tabla
class TableValidateTypeInheritanceComponent(FlowComponent[T]):
    """
    Las clases pueden tener herencia cruzada por ejemplo heredar de un composite y table
    a la vez, esto es ilegal, esta validacion la corremos al momento de definir el 
    core_schema de pydantic para asegurarnos que el PGRepresentable es valido y 
    su definicion univoca
    """

    def __init__(self, base_class: type):
        super().__init__('validate-type-inheritance-component')

    def execute(self, cls: type, accumulator: FlowAccumulator) -> None:
        pass


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


class TableValidateRestrictedMetadataTypesComponent(FlowComponent[pg_table]):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self, restricted: list[type]):
        super().__init__('validate-restricted-metadata-types-component')
        self._restricted = restricted

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        for name, info in target.model_fields.items():
            for meta in info.metadata:
                meta_type: type = type(meta)
                if meta_type not in self._restricted:
                    errors.append(f'Invalid metadata type {meta_type} in {name} declaration')
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)


class TableValidateUniqueMetadataTypesComponent(FlowComponent[pg_table]):
    """
    Types received must appear once in field metadata
    """

    def __init__(self, unique: list[type]):
        super().__init__('validate-unique-metadata-type-component')
        self._unique = unique

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        # extract_by_instance_type_from_model_fields_info debe obtener toda la metadata
        # hasta el type basico subyacente. por ejemplo de pg_int hasta el type
        # int subyacente
        for name, info in target.model_fields.items():
            classified_field_meta: dict[type, int] = get_field_classified_metadata_appearances(info)
            for unique in self._unique:
                appearances: int = classified_field_meta.get(unique, 0)
                if appearances > 1:
                    errors.append(f'Metadata type {unique.__name__} can only appear once in {name} declaration')
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)


class TableValidateBaseTypesComponent(FlowComponent[pg_table]):
    """
    We must be sure that base type of fields will have a postgres representation
    """

    def __init__(self, required: list[type]):
        super().__init__('validate-required-metadata-types-component')
        self._required = required

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        # mira el type base del campo y valida que este entre los requeridos
        errors: list[str] = []
        super_types: str = ', '.join([e.__name__ for e in self._required])
        for name, info in target.model_fields.items():
            is_subclass_of_required: bool = False
            for required in self._required:
                if issubclass(info.annotation, required) or isinstance(info.annotation, pg_builtin):
                    is_subclass_of_required = True
            if not is_subclass_of_required:
                errors.append(f'Field {name} must be a subtype of {super_types}')
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)


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
                errors.append(f'Inherited class {base_class} must be a subclass of {pg_target.__name__}')
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)


class TableValidateConsistentForeignKeysComponent(FlowComponent[pg_table]):
    """
    We must ensure that target definition inherits from classes
    with the same base class
    """

    def __init__(self):
        super().__init__('validate-consistent-foreign-keys-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        for base_class in extract_by_instance_type_from_inherited_classes(target, pg_table):
            if not issubclass(base_class, pg_table):
                errors.append(f'Inherited class {base_class} must be a subclass of {pg_target.__name__}')
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)


# table_validate_declaration_stage = Stage(
#     name='validate-declaration-stage',
#     aspect_generator=identity_generator)
# pgdriver_pgtable_definition_flow.register(table_validate_declaration_stage)
class TableExtractIndexDefinitionFromDeclarationComponent(FlowComponent[pg_table]):
    # un campo solo puede tener una declaracion de builtin
    def __init__(self):
        super().__init__('extract-index-definition-from-declaration-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
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
            accumulator.add_definition('indexes', [aggregate(grouped_by_name[ix_name], {
                    'ix_column': ordered_set_accumulator}) for ix_name in grouped_by_name])
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])


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
            accumulator.add_definition('primary_keys', [aggregate(grouped_by_name[pk_name], {
                    'pk_column': ordered_set_accumulator}) for pk_name in grouped_by_name])
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])


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
            accumulator.add_definition('foreign_keys', [aggregate(grouped_by_name[fk_name], {
                    'fk_column': ordered_set_accumulator,
                    'fk_other_class_column_name': ordered_set_accumulator}) for fk_name in grouped_by_name])
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])


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
            accumulator.add_definition('unique_indexes', [aggregate(grouped_by_name[uix_name], {
                    'uix_column': ordered_set_accumulator}) for uix_name in grouped_by_name])
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])


class TableExtractInheritanceDefinitionFromDeclarationComponent(FlowComponent[pg_table]):
    # un campo solo puede tener una declaracion de builtin
    def __init__(self):
        super().__init__('extract-inheritance-definition-from-declaration-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        try:
            inherited: list[type] = extract_by_instance_type_from_inherited_classes(
                target,
                pg_table)
            accumulator.add_definition('inherited', inherited)
        except Exception as e:
            raise FlowComponentException(self.name, [str(e)])


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
                col_data['col_check'] = check.predicate.as_str(name)
            comment: Optional[pg_comment_meta] = extract_first_instance_from_field_metadata(info, pg_comment_meta)
            if comment is not None:
                col_data['col_comment'] = comment.value
            columns.append(col_data)
        accumulator.add_definition('columns', columns)


class TableValidateExtractedForeignKeyDefinitionComponent(FlowComponent[pg_table]):
    """
    Validates that extracted foreign keys columns are columns of the
    same type in the other class
    """

    def __init__(self):
        super().__init__('validate-extracted-foreign-key-definition-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        fks: list[dict[str, Any]] = accumulator.definition.get('foreign_keys', [])
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


class TableValidateExtractedUniqueIndexDefinitionComponent(FlowComponent[pg_table]):
    """
    Validates that a column doesnt appear in more than one unique index definition
    """

    def __init__(self):
        super().__init__('validate-extracted-unique-index-definition-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        uixs: list[dict[str, Any]] = accumulator.definition.get('unique_indexes', [])
        columns: Optional[OrderedSet[str]] = None
        for uix_definition in uixs:
            if columns is None:
                columns = uix_definition['uix_column']
            else:
                if columns.intersection(uix_definition['uix_column']).count() > 0:
                    message: str = 'Column appears in more than one unique index definition'
                    raise FlowComponentException(self.name, [message])


class TableValidateExtractedPrimaryKeyDefinitionComponent(FlowComponent[pg_table]):
    """
    Validates that a column doesnt appear in more than one primary key definition
    """

    def __init__(self):
        super().__init__('validate-extracted-primary-key-definition-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        pks: list[dict[str, Any]] = accumulator.definition.get('primary_keys', [])
        columns: Optional[OrderedSet[str]] = None
        for pk_definition in pks:
            if columns is None:
                columns = pk_definition['pk_column']
            else:
                if columns.intersection(pk_definition['pk_column']).count() > 0:
                    message: str = 'Column appears in more than one primary key definition'
                    raise FlowComponentException(self.name, [message])
