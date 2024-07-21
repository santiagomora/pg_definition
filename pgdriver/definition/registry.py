from .flow import\
    DefinitionFlow,\
    FlowAccumulator
from heapq import\
    heappush,\
    heappop
from typing import\
    Any


# se asocia el definition context del type con el definition context del type padre
# se asume que el type a registrar es parte de una definicion valida
class DefinitionFlowRegistry:
    def __init__(self, name: str) -> None:
        self._name = name
        self._flows: dict[type, DefinitionFlow] = {}

    def register_definition_flow(self, flow: DefinitionFlow) -> None:
        if flow.target in self._flows:
            raise Exception(f'Context registry: {flow.target} definition flow already defined: {self[flow.target]._name}')
        self._flows[flow.target] = flow

    def execute_definition_flow(self, on_type: type) -> dict[Any, Any]:
        execute_flows: list[DefinitionFlow] = []
        accumulator: FlowAccumulator = FlowAccumulator(on_type)
        for flow_target in self._flows:
            if issubclass(on_type, flow_target):
                heappush(execute_flows, self._flows[flow_target])
        if len(execute_flows) == 0:
            raise Exception(f'Context registry: definition flows not defined for {on_type}')
        while len(execute_flows) > 0:
            flow = heappop(execute_flows)
            flow.execute(on_type, accumulator)
        return accumulator
