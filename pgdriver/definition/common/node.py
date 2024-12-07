from .flow import\
    SingleChoiceDefinitionFlowNode,\
    NodeException,\
    FlowAccumulator,\
    MultipleChoiceDefinitionFlowNode
from .inspection import\
    extract_definition_fields,\
    extract_type
from typing import\
    Optional
from typing import\
    Iterator
from pydantic.fields import\
    FieldInfo


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
            is_subclass_of_required: bool = False
            for required in self._type_subclass:
                if issubclass(extract_type(info.annotation), required):
                    is_subclass_of_required = True
            is_instance_of_required: bool = False
            if not is_subclass_of_required:
                for required in self._type_instance:
                    if isinstance(extract_type(info.annotation), required):
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

    def __init__(self, name: str, base_class: type):
        super().__init__(2, name)
        self._base_class = base_class
        self.is_domain: Optional[bool] = None

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        base_class: tuple[type] = target.__bases__[0]
        self.is_domain = base_class is not self._base_class
