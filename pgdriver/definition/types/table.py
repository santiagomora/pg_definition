from typing import\
    Optional
from collections import\
    OrderedDict
from pgdriver.definition.flow import\
    FlowComponent,\
    FlowAccumulator,\
    DefinitionFlow,\
    FlowAccumulatorErrorsPolicy,\
    FlowComponentException
from pgdriver.definition.types.metadata import\
    pg_foreign_key,\
    pg_primary_key,\
    pg_index,\
    pg_unique,\
    pg_check,\
    pg_comment
from pgdriver.definition.types.builtin import\
    pg_builtin
from typing import\
    Any
from .representable import\
    PGRepresentable
from .enum import\
    pg_enum
from .composite import\
    pg_composite
from .domain import\
    pg_domain
from pgdriver.adapt.pydantic import\
    PGBaseModel
from pgdriver.definition.inspection import\
    extract_by_instance_type_from_model_fields_info,\
    aggregate,\
    ordered_set_accumulator,\
    key_by,\
    get_field_classified_metadata_appearances,\
    extract_by_instance_type_from_inherited_classes,\
    extract_first_instance_from_field_metadata
from abc import\
    ABC
from pydantic.fields import\
    FieldInfo
import deepdiff
from ordered_set import\
    OrderedSet


class PGCheckDefinition:
    pass


class PGTriggerDefinition:
    pass


class PGIndexDefinition:
    pass


class PGUniqueIndexDefinition:
    pass


class PGColumnDefinition:
    pass


class PGPrimaryKeyDefinition:
    pass


class PGForeignKeyDefinition:
    pass


class PGTableDefinition:
    comment:           Optional[str] = None
    columns:           Optional[OrderedDict[PGColumnDefinition, None]] = None
    indexes:           Optional[dict[str, PGIndexDefinition]] = None
    unique_indexes:    Optional[dict[str, PGUniqueIndexDefinition]] = None
    foreign_keys:      Optional[dict[str, PGForeignKeyDefinition]] = None
    primary_keys:      Optional[dict[str, PGPrimaryKeyDefinition]] = None
    base_tables:       Optional[tuple[type]] = None
    triggers:          Optional[PGTriggerDefinition] = None


# hay un detalle en hacerlo de esta manera, una tabla de postgres puede tener herencia 
# multiple, para que no haya conflicto en las definiciones, me parece que tendremos que 
# crear una tercera clase con los merge de las clases base y aplicarla sobre la clase final
class pg_table(PGBaseModel, PGRepresentable[PGTableDefinition], ABC):
    pass


pgtable_definition_flow: DefinitionFlow[pg_table] = DefinitionFlow[pg_table]('pgdriver-table-definition-flow', pg_table)


class ValidateRestrictedMetadataTypesComponent(FlowComponent[pg_table]):
    """
    Metadata in fields are restricted to the restricted instances
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


class ValidateUniqueMetadataTypesComponent(FlowComponent[pg_table]):
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


class ValidateBaseTypesComponent(FlowComponent[pg_table]):
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


class ValidateInheritedFieldsComponent(FlowComponent[pg_table]):
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


class ValidateConsistentBaseClassesComponent(FlowComponent[pg_table]):
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


class ValidateConsistentForeignKeysComponent(FlowComponent[pg_table]):
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


pgtable_definition_flow.register_component(
    ValidateConsistentBaseClassesComponent())


pgtable_definition_flow.register_component(
    ValidateInheritedFieldsComponent())


# metadata sobre types base de metadata, es la primera que debe ir.
# en cierto momento se me ocurrio chequear los type base de la definicion
# pero pasa que el type base puede tener n niveles. no hay limite de nesting
# en postgres para definir dominios por lo cual estas definiciones de campo 
# se aplican sobre el unnesting completo del type hasta llegar a lo mas primitivo
pgtable_definition_flow.register_component(
    ValidateRestrictedMetadataTypesComponent([
        pg_foreign_key,
        pg_primary_key,
        pg_index,
        pg_unique,
        pg_check,
        pg_comment]))

# no incluyo pg_comment porque uno de los types de tabla puede 
# ser un composite o un domain con un comentario, y el campo en la tabla podria definir
# un comentario adicional
# esto debe aplicarse sobre la definicion completa del type, expandiendo el type base
pgtable_definition_flow.register_component(
    ValidateUniqueMetadataTypesComponent([
        pg_foreign_key,
        pg_primary_key,
        pg_unique,
        pg_comment,
        pg_check]))

# me asegura que solo se usen los types base al definir la tabla
# aqui puedo iundicar un pg_composite y pg_built_in_identifier ademas 
# ya no se verifica la presencia de una instancia de metadata, sino 
# que herede de pg_built_in_identifier o pg_composite o pg_enum
pgtable_definition_flow.register_component(
    ValidateBaseTypesComponent([
        pg_enum,
        pg_composite,
        pg_domain]))


# table_validate_declaration_stage = Stage(
#     name='validate-declaration-stage',
#     aspect_generator=identity_generator)
# pgdriver_pgtable_definition_flow.register(table_validate_declaration_stage)
class ExtractIndexDefinitionFromDeclarationComponent(FlowComponent[pg_table]):
    # un campo solo puede tener una declaracion de builtin
    def __init__(self):
        super().__init__('extract-index-definition-from-declaration-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        indexes: list[dict[str, Any]] = extract_by_instance_type_from_model_fields_info(
            target.model_fields,
            pg_index,
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


class ExtractPrimaryKeyDefinitionFromDeclarationComponent(FlowComponent[pg_table]):
    # un campo solo puede tener una declaracion de builtin
    def __init__(self):
        super().__init__('extract-primary-key-definition-from-declaration-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        pks: list[dict[str, Any]] = extract_by_instance_type_from_model_fields_info(
            target.model_fields,
            pg_primary_key,
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


class ExtractForeignKeyDefinitionFromDeclarationComponent(FlowComponent[pg_table]):
    # un campo solo puede tener una declaracion de builtin
    def __init__(self):
        super().__init__('extract-foreign-key-definition-from-declaration-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        fks: list[dict[str, Any]] = extract_by_instance_type_from_model_fields_info(
            target.model_fields,
            pg_foreign_key,
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


class ExtractUniqueIndexDefinitionFromDeclarationComponent(FlowComponent[pg_table]):
    # un campo solo puede tener una declaracion de builtin
    def __init__(self):
        super().__init__('extract-unique-index-definition-from-declaration-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        uixs: list[dict[str, Any]] = extract_by_instance_type_from_model_fields_info(
            target.model_fields,
            pg_unique,
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


class ExtractInheritanceDefinitionFromDeclarationComponent(FlowComponent[pg_table]):
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


class ExtractColumnDefinitionFromDeclarationComponent(FlowComponent[pg_table]):
    def __init__(self):
        super().__init__('extract-column-definition-from-declaration-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        # extraer las definiciones de columna
        columns: list[dict[str, Any]] = []
        for name, info in target.model_fields.items():
            check: Optional[pg_check] = extract_first_instance_from_field_metadata(info, pg_check)
            col_data: dict[str, Any] = {
                'col_name': name,
                'col_type': info.annotation}
            if check is not None:
                col_data['col_check'] = check.predicate.as_str(name)
            comment: Optional[pg_comment] = extract_first_instance_from_field_metadata(info, pg_comment)
            if comment is not None:
                col_data['col_comment'] = comment.value
            columns.append(col_data)
        accumulator.add_definition('columns', columns)


# NOTE a esta etapa entra el objeto acumulador con todos los fallos de la etapa 
# de validacion de declaraciones. si hay errores levanta la excepcion y rompe
# el flujo asociado a la tabla
# agrega a la definicion de tabla la metadata sobre fks, pks, indices, etc
pgtable_definition_flow.register_component(
    ExtractIndexDefinitionFromDeclarationComponent())

pgtable_definition_flow.register_component(
    ExtractPrimaryKeyDefinitionFromDeclarationComponent())

pgtable_definition_flow.register_component(
    ExtractForeignKeyDefinitionFromDeclarationComponent())

pgtable_definition_flow.register_component(
    ExtractUniqueIndexDefinitionFromDeclarationComponent())

pgtable_definition_flow.register_component(
    ExtractInheritanceDefinitionFromDeclarationComponent())

pgtable_definition_flow.register_component(
    ExtractColumnDefinitionFromDeclarationComponent())


pgtable_definition_flow.set_critical_component('extract-index-definition-from-declaration-component')


class ValidateExtractedForeignKeyDefinitionComponent(FlowComponent[pg_table]):
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


class ValidateExtractedUniqueIndexDefinitionComponent(FlowComponent[pg_table]):
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


class ValidateExtractedPrimaryKeyDefinitionComponent(FlowComponent[pg_table]):
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


pgtable_definition_flow.register_component(
    ValidateExtractedForeignKeyDefinitionComponent())

pgtable_definition_flow.register_component(
    ValidateExtractedUniqueIndexDefinitionComponent())

pgtable_definition_flow.register_component(
    ValidateExtractedPrimaryKeyDefinitionComponent())


pgtable_definition_flow.set_critical_component('validate-extracted-foreign-key-definition-component')


class StoreDefinitionInTargetComponent(FlowComponent[pg_table]):
    def __init__(self):
        super().__init__('store-definition-in-target-component')

    def execute(self, target: type[pg_table], accumulator: FlowAccumulator) -> None:
        # chequear si hay algun error acumulado, si no lo hay la definicion es valida
        # y puedo generar la instancia de TableDefinition
        pass


pgtable_definition_flow.register_component(
    StoreDefinitionInTargetComponent())


pgtable_definition_flow.set_critical_component('store-definition-in-target-component')
