from .flow import\
    FlowAccumulator,\
    MultipleChoiceDefinitionFlowNode
from typing import\
    Optional


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
        self.is_domain = hasattr(target, 'base_type')


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
