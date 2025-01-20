from .flow import\
    SingleChoiceDefinitionFlowNode,\
    NodeException,\
    FlowAccumulator,\
    MultipleChoiceDefinitionFlowNode
from .inspection import\
    extract_definition_fields
from typing import\
    Optional
from .inspection import\
    is_pg_type,\
    get_field_classified_metadata_appearances,\
    extract_inherited_fields,\
    extract_by_instance_type_from_model_fields_info


class CommonValidateFieldsBaseTypeNode(SingleChoiceDefinitionFlowNode):
    """
    We must be sure that base type of fields will have a postgres representation
    """

    def __init__(
        self, name: str, *, type_subclass: list[type],
        type_instance: list[type]
    ) -> None:
        super().__init__(name)
        self._type_subclass = type_subclass
        self._type_instance = type_instance

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        # mira el type base del campo y valida que este entre los requeridos
        errors: list[str] = []
        for name, info in extract_definition_fields(target):
            errors += is_pg_type(
                name, info.annotation, self._type_subclass, self._type_instance
            )
        if len(errors) > 0:
            raise NodeException(self.name, errors)


class CommonValidateRestrictedMetadataTypesNode(SingleChoiceDefinitionFlowNode):
    """
    Metadata in fields are restricted to the passed instances
    """

    def __init__(
        self, name: str, *, types: list[type]
    ):
        super().__init__(name)
        self._restricted = types

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        for name, info in extract_definition_fields(target):
            for meta in info.metadata:
                meta_type: type = type(meta)
                if meta_type not in self._restricted:
                    errors.append(f'Invalid metadata type {meta_type} in {name} declaration')
        if len(errors) > 0:
            raise NodeException(self.name, errors)


class CommonDetermineIfTargetIsDomainNode(MultipleChoiceDefinitionFlowNode):
    """
    Types can only inherit from base_class, if they inherit from a subclass of the 
    base class, then they will be considered as domain. A definition in the accumulator
    will be added accordingly
    """

    def __init__(self, name: str):
        super().__init__(2, name)
        self.is_domain: Optional[bool] = None

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        self.is_domain = hasattr(target.__bases__[0], '__pg_definition')


class CommonDetermineIfObjectIsDomainNode(MultipleChoiceDefinitionFlowNode):
    """
    Types can only inherit from base_class, if they inherit from a subclass of the 
    base class, then they will be considered as domain. A definition in the accumulator
    will be added accordingly
    """

    def __init__(self, name: str, base_type: type):
        super().__init__(2, name)
        self.is_domain: Optional[bool] = None
        self._base_type = base_type

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        self.is_domain = target.__bases__[0] != self._base_type


class ModelValidateUniqueMetadataTypesNode(SingleChoiceDefinitionFlowNode):
    """
    Types received must appear once in field metadata
    """

    def __init__(self, name: str, *, types: list[type]):
        super().__init__(name)
        self._unique = types

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        # extract_by_instance_type_from_model_fields_info debe obtener toda la metadata
        # hasta el type basico subyacente. por ejemplo de int4 hasta el type
        # int subyacente
        for name, info in extract_definition_fields(target):
            classified_field_meta: dict[type, int] = get_field_classified_metadata_appearances(info)
            for unique in self._unique:
                appearances: int = classified_field_meta.get(unique, 0)
                if appearances > 1:
                    errors.append(f'Metadata type {unique} can only appear once in {name} declaration')
        if len(errors) > 0:
            raise NodeException(self.name, errors)


class ModelDiscardMetaInstancesFromInheritedFieldsNode(SingleChoiceDefinitionFlowNode):
    """
    All inherited metadata gets discarded. Initially it was planned to keep check and default values, but as parent validation gets applied when creating an instance, this is not necessary.
    Postgres itself will be in charge to add all parent check constraints by itself when declaring the inheritance over the child class.
    """

    def __init__(self, name: str):
        super().__init__(name)

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        pass
        # for field, info in extract_inherited_fields(target):
        #     target.model_fields[field].metadata = []
        # target.model_rebuild(force=True)


class ModelValidateSameTypeMetaInstancesHaveDifferentNamesNode(SingleChoiceDefinitionFlowNode):
    def __init__(self, name: str, *, types: tuple[type, ...]):
        super().__init__(name)
        self._types = types

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        name_count: dict[str, int] = {}
        errors: list[str] = []
        for tp in self._types:
            for field_name, instance in extract_by_instance_type_from_model_fields_info(target, tp):
                abs_name: str = f'{field_name}.{instance.name}.{tp.__name__}'
                name_count[abs_name] = name_count.get(abs_name, 0) + 1
        for name in name_count:
            if name_count[name] > 1:
                field_name, instance_name, tp_name = name.split('.')
                # this means there is two instances of same type that share name
                errors.append(f'Metadata definition error in {field_name}: found {name_count[name]} repeated instances of same type {tp_name} sharing name {instance_name}.')
        if len(errors) > 0:
            raise NodeException(self.name, errors)
