from collections import\
    OrderedDict
from abc import\
    ABC,\
    abstractmethod
from typing import\
    Any,\
    Optional,\
    Generic,\
    TypeVar
from typing_extensions import\
    Self
from enum import\
    Enum,\
    auto
import pprint
from heapq import\
    heappush,\
    heappop


# para domains cambia un poco porque entra por metaclase, con lo cual issubclass va a fallar


class FlowComponentException(Exception):
    def __init__(self, name, error_list):
        super().__init__(f'Error in component {name}')
        self.error_list = error_list
        self.component_name = name


class FlowEndException(Exception):
    pass


class FlowAccumulatorErrorsPolicy(Enum):
    LOG_INFO = auto()
    END_FLOW = auto()


T = TypeVar('T')


class FlowAccumulator:
    def __init__(self, on_type: type) -> None:
        self._definition = dict[Any, Any]()
        self._on_type = on_type
        self._errors = dict[str, dict[str, FlowComponentException]]()

    def __str__(self):
        errors: list[str] = []
        for flow in self._errors:
            errors.append(f'Errors in flow: {flow}')
            cmp_errors: list[str] = []
            for component in self._errors[flow]:
                cmp_errors.append(f'\tErrors in component: {component}:')
                cmp_errors += [f'\t\t{str(e)}' for e in self._errors[flow][component].error_list]
            errors.append('\n\t'.join(cmp_errors))
        definition: str = pprint.pformat(self._definition)
        error_str: str = '\n\t'.join(errors)
        return f'Flow accumulator for type {self._on_type}:\nDefinition:\n{definition}\nErrors:\n\t{error_str}'

    @property
    def definition(self) -> dict[Any, Any]:
        return self._definition

    @property
    def errors(self) -> dict[Any, Any]:
        return self._errors

    def clear(self) -> None:
        self._definition.clear()
        self._errors.clear()

    def has_errors(self):
        return len(self._errors.keys()) != 0

    def add_definition(self, name: str, definition: Any) -> Self:
        if name in self._definition:
            raise Exception(f'Existing definition for {name} in accumulator.')
        self._definition[name] = definition
        return self

    def add_exception(self, flow_name: str, exception: FlowComponentException) -> Self:
        flow_errors = self._errors.get(flow_name, {})
        flow_errors[exception.component_name] = exception
        self._errors[flow_name] = flow_errors
        return self


class FlowComponent(ABC, Generic[T]):
    def __init__(self, name: str) -> None:
        self._name = name
        self._accumulator_errors_policy = FlowAccumulatorErrorsPolicy.LOG_INFO

    @property
    def name(self) -> str:
        return self._name

    def set_accumulator_policy(self, accumulator_errors_policy: FlowAccumulatorErrorsPolicy) -> Self:
        self._accumulator_errors_policy = accumulator_errors_policy
        return self

    def initialize(self, accumulator: FlowAccumulator) -> None:
        if not accumulator.has_errors():
            return
        if self._accumulator_errors_policy == FlowAccumulatorErrorsPolicy.END_FLOW:
            raise FlowEndException(f'Errors detected when initializing component "{self._name}". Accumulator:\n{str(accumulator)}')

    @abstractmethod
    def execute(self, target: type[T], accumulator: FlowAccumulator) -> None:
        pass


# el definition flow es un heap tambien
class DefinitionFlow(Generic[T]):
    def __init__(self, name: str, target: type[T]) -> None:
        self._name = name
        self._target = target
        self._components: OrderedDict[str, FlowComponent[T]] = OrderedDict()

    @property
    def target(self) -> type[T]:
        return self._target

    @property
    def name(self) -> str:
        return self._name

    def __repr__(self):
        return f'FlowComponent(target={self.target})'

    def __lt__(self, other: 'DefinitionFlow') -> bool:
        return issubclass(other.target, self.target)

    def set_critical_component(self, component_name: str) -> None:
        if component_name not in self._components:
            raise Exception('Critical component not defined.')
        self._components[component_name].set_accumulator_policy(FlowAccumulatorErrorsPolicy.END_FLOW)

    def register_component(self, component: FlowComponent[T]) -> None:
        if component.name in self._components:
            raise Exception(f'Element of type {type(component)} already declared')
        existing_elem_of_type: Optional[str] = None
        for name, comp in self._components.items():
            if type(comp) == type(component):
                existing_elem_of_type = component.name
                break
        if existing_elem_of_type is not None:
            raise Exception(f'Component of type {type(component)} already declared in flow {self._name} with name {existing_elem_of_type}')
        self._components[component.name] = component
        self._components.move_to_end(component.name)

    def execute(self, on_type: type[T], accumulator: FlowAccumulator) -> None:
        if not issubclass(on_type, self._target):
            raise Exception(f'Type {on_type} must be a subclass of {self.target} to be executed in flow {self.name}')
        for name, component in self._components.items():
            try:
                component.initialize(accumulator)
                component.execute(on_type, accumulator)
            except FlowComponentException as e:
                accumulator.add_exception(self._name, e)
            except FlowEndException as e:
                raise e


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
