from .flow import\
    SingleChoiceDefinitionFlowNode,\
    FlowAccumulator,\
    FlowNodeException,\
    MultipleChoiceDefinitionFlowNode
from typing import\
    Optional


class CommonValidateSingleInheritedClassNode(SingleChoiceDefinitionFlowNode):
    def __init__(self, name: str):
        super().__init__(name)

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        base_classes: tuple[type] = target.__bases__
        if len(base_classes) > 1:
            raise FlowNodeException(self.name, [f'Type {target} can only have one base class'])


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
