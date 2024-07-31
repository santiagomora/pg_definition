from pgdriver.definition.flows import\
    FlowComponent,\
    FlowAccumulator,\
    FlowComponentException
from pgdriver.definition.inspection import\
    get_field_classified_metadata_appearances,\
    extract_by_instance_type_from_inherited_classes
from pgdriver.definition.flows import\
    T
from pgdriver.definition.build import\
    pg_check_meta,\
    pg_check
from typing import\
    Any
from pgdriver.definition.inspection import\
    extract_by_instance_type_from_model_fields_info,\
    has_classmethod


class CommonValidateRestrictedMetadataTypesComponent(FlowComponent[T]):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(self, restricted: list[type]):
        super().__init__('validate-restricted-metadata-types-component')
        self._restricted = restricted

    def execute(self, target: type[T], accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        for name, info in target.model_fields.items():
            for meta in info.metadata:
                meta_type: type = type(meta)
                if meta_type not in self._restricted:
                    errors.append(f'Invalid metadata type {meta_type} in {name} declaration')
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)


class CommonValidateUniqueMetadataTypesComponent(FlowComponent[T]):
    """
    Types received must appear once in field metadata
    """

    def __init__(self, unique: list[type]):
        super().__init__('validate-unique-metadata-type-component')
        self._unique = unique

    def execute(self, target: type[T], accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        # extract_by_instance_type_from_model_fields_info debe obtener toda la metadata
        # hasta el type basico subyacente. por ejemplo de pg_int hasta el type
        # int subyacente
        for name, info in target.model_fields.items():
            classified_field_meta: dict[type, int] = get_field_classified_metadata_appearances(info)
            for unique in self._unique:
                appearances: int = classified_field_meta.get(unique, 0)
                if appearances > 1:
                    errors.append(f'Metadata type {unique} can only appear once in {name} declaration')
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)


class CommonValidateSingleInheritedClassComponent(FlowComponent[T]):
    """
    Types can only inherit from base_class
    """

    def __init__(self):
        super().__init__('validate-single-inherited-class-component')

    def execute(self, target: type[T], accumulator: FlowAccumulator) -> None:
        base_classes: tuple[type] = extract_by_instance_type_from_inherited_classes(
            target)
        if len(base_classes) > 1:
            raise FlowComponentException(self.name, f'Type {target} can only have one base class: {self._base_class}')
        base_class: type = base_classes[0]
        if base_class != self._base_class:
            raise FlowComponentException(self.name, f'Type {target} base class must be: {self._base_class}')


class CommonValidateFieldsBaseTypeComponent(FlowComponent[T]):
    """
    We must be sure that base type of fields will have a postgres representation
    """

    def __init__(self, *, type_subclass: list[type], type_instance: list[type]):
        super().__init__('validate-base-type-component')
        self._type_subclass = type_subclass
        self._type_instance = type_instance

    def execute(self, target: type[T], accumulator: FlowAccumulator) -> None:
        # mira el type base del campo y valida que este entre los requeridos
        errors: list[str] = []
        for name, info in target.model_fields.items():
            is_subclass_of_required: bool = False
            for required in self._type_subclass:
                if issubclass(info.annotation, required):
                    is_subclass_of_required = True
            is_instance_of_required: bool = False
            if not is_subclass_of_required:
                for required in self._type_instance:
                    if isinstance(info.annotation, required):
                        is_instance_of_required = True
            if is_subclass_of_required or is_instance_of_required:
                continue
            elif not is_instance_of_required:
                super_instances_str: str = ', '.join([str(e) for e in self._type_instance])
                errors.append(f'Field {name} type must be a subclass of {super_instances_str}')
            else:
                super_classes_str: str = ', '.join([str(e) for e in self._type_subclass])
                errors.append(f'Field {name} type must be an instance of {super_classes_str}')
        if len(errors) > 0:
            raise FlowComponentException(self.name, errors)


class CommonExtractCheckConstraintsComponent(FlowComponent[T]):
    """
    Extracts check constraint from fields
    """

    def __init__(self):
        super().__init__('extract-check-constraints-component')

    def execute(self, target: type[T], accumulator: FlowAccumulator) -> None:
        constraints: list[pg_check_meta] = [const for const in extract_by_instance_type_from_model_fields_info(
            target,
            pg_check_meta,
            self._base_class,
            lambda field_name, ck: {
                'ck_check_meta': ck,
                'ck_field_name': field_name})]
        if len(constraints) > 0:
            accumulator.add_definition('check_constraints', constraints)


class CommonStoreCheckConstraintsComponent(FlowComponent[T]):
    """
    Stores check constraint extracted from fields
    """

    def __init__(self):
        super().__init__('store-check-constraints-component')

    def execute(self, target: type[T], accumulator: FlowAccumulator) -> None:
        definition: list[dict[str, Any]] = accumulator.get_definition('check_constraints', 'extraction')
        if definition is None:
            return
        cks: list[pg_check] = [pg_check(**ck) for ck in definition]

        @classmethod
        def __pg_check_constraints(cls) -> list[pg_check]:
            return cks

        accumulator.add_definition('__pg_check_constraints', __pg_check_constraints)


class ValidatesConflictingDefinitions:
    """
    Used to validate that inferred definitions fon interfere with 
    those injected through decorators
    """

    def check_conflicting_definitions(self, target: type, definition_name: str) -> None:
        if has_classmethod(target, f'__pg_{definition_name}'):
            raise FlowComponentException(target.name, [f'Conflicting definition {definition_name} for component {self._name}'])
