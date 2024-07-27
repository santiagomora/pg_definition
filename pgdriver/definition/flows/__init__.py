from collections import\
    OrderedDict
from abc import\
    ABC,\
    abstractmethod
from typing import\
    Any,\
    Optional,\
    Generic,\
    TypeVar,\
    get_args,\
    Callable,\
    ContextManager
from typing_extensions import\
    Self
from enum import\
    Enum,\
    auto
import pprint
from heapq import\
    heappush,\
    heappop
from contextlib import\
    contextmanager


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


class HandlesWorkPath:
    def __init__(self):
        self._work_path = ''

    @contextmanager
    def at_work_path(self, name) -> ContextManager[Self]:
        old_path: str = self._work_path
        self._work_path = name if self._work_path == '' else f'{self._work_path}.{name}'
        yield self
        self._work_path = old_path


class FlowAccumulator(HandlesWorkPath):
    def __init__(self, on_type: type) -> None:
        super().__init__(self)
        self._definition = dict[Any, Any]()
        self._on_type = on_type

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
    def errors(self) -> dict[Any, Any]:
        return self._errors

    def clear(self) -> None:
        self._definition.clear()
        self._errors.clear()

    def has_errors(self):
        return len(self._errors.keys()) != 0

    def get_definition(self, name: str, abspath: Optional[str] = None) -> Optional[Any]:
        if abspath is None:
            return self._definition[name]
        dic: dict[str, Any] = self._definition
        path: list[str] = self._work_path.split('.')
        for ix in range(0, len(path)):
            at: str = path[ix]
            if at not in dic:
                return None
            if not isinstance(dic[at],  dict):
                err_path: str = '.'.join(path[0:ix]) + at
                raise Exception(f'Accessing invalid level at definition flow: {err_path}')
            dic = dic[at]
        dic: dict[str, Any] = self._go_to_path(abspath)
        return None if name not in dic else dic[name]

    def add_definition(self, name: str, definition: Any) -> Self:
        dic: dict[str, Any] = self._definition
        path: list[str] = self._work_path.split('.')
        for ix in range(0, len(path)):
            at: str = path[ix]
            if at in dic:
                if type(dic[at]) != dict:
                    err_path: str = '.'.join(path[0:ix]) + at
                    raise Exception(f'Invalid level detected at definition flow: {err_path}')
                dic = dic[at]
            else:
                dic[at] = {}
        if name in dic:
            raise Exception('Cant modify existing key')
        dic[name] = definition
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

    def critical(self) -> Self:
        self._accumulator_errors_policy = FlowAccumulatorErrorsPolicy.END_FLOW
        return self

    def initialize(self, accumulator: FlowAccumulator) -> None:
        if not accumulator.has_errors():
            return
        if self._accumulator_errors_policy == FlowAccumulatorErrorsPolicy.END_FLOW:
            raise FlowEndException(f'Errors detected when initializing component "{self._name}". Accumulator:\n{str(accumulator)}')

    @abstractmethod
    def execute(self, target: type[T], accumulator: FlowAccumulator) -> None:
        pass

    @abstractmethod
    def get_dependencies(self) -> tuple[str]:
        pass


class DefinitionFlow(HandlesWorkPath, Generic[T]):
    def __init__(self, name: str) -> None:
        self._name = name
        self._target = get_args(self.__orig_class__)[0]
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
        return self.is_subordinate(other)

    def register(self, component: FlowComponent[T]) -> None:
        if component.name in self._components:
            raise Exception(f'Element of type {type(component)} already declared')
        existing_elem_of_type: Optional[str] = None
        for name, comp in self._components.items():
            if type(comp) == type(component):
                existing_elem_of_type = component.name
                break
        if existing_elem_of_type is not None:
            raise Exception(f'Component of type {type(component)} already declared in flow {self._name} with name {existing_elem_of_type}')
        dependencies: set[str] = set(component.get_dependencies())
        existing: set[str] = set(self._components.keys())
        if existing.intersection(dependencies).count() != dependencies.count() and dependencies.count() != 0:
            missing: str = ", ".join(dependencies.difference(existing))
            raise Exception(f'Dependencies not met for component "{component.name}", missing: {missing}')
        component.accumulator_path = self._work_path
        self._components[component.name] = component
        self._components.move_to_end(component.name)

    def execute(self, on_type: type[T], accumulator: FlowAccumulator) -> None:
        if not issubclass(on_type, self._target):
            raise Exception(f'Type {on_type} must be a subclass of {self.target} to be executed in flow {self.name}')
        i: int = 0
        j: int = 0
        components: list[FlowComponent[T]] = self._components.values()
        while i < len(components):
            j = i
            last_accumulator_path: str = components[j]. accumulator_path
            with accumulator.at_work_path(last_accumulator_path) as acc:
                while j < len(components) and last_accumulator_path == components[j].accumulator_path:
                    try:
                        components[j].initialize(acc)
                        components[j].execute(on_type, acc)
                    except FlowComponentException as e:
                        accumulator.add_exception(self._name, e)
                    except FlowEndException as e:
                        raise e
                    j += 1
            i = j

    @abstractmethod
    def is_subordinate(self, other: 'DefinitionFlow'):
        pass


class TypeSubclassDefinitionFlow(DefinitionFlow[T]):
    def is_subordinate(self, other: 'DefinitionFlow'):
        return issubclass(self.target, other.target)


class TypeInstanceDefinitionFlow(DefinitionFlow[T]):
    def is_subordinate(self, other: 'DefinitionFlow'):
        return isinstance(self.target, other.target)


# se asocia el definition context del type con el definition context del type padre
# se asume que el type a registrar es parte de una definicion valida
class DefinitionFlowRegistry:
    def __init__(self, name: str) -> None:
        self._name = name
        self._flows: dict[type, DefinitionFlow] = {}

    def register(self, flow: DefinitionFlow) -> None:
        if flow.target in self._flows:
            raise Exception(f'Context registry: {flow.target} definition flow already defined: {self[flow.target]._name}')
        self._flows[flow.target] = flow

    def execute_flow(self, on_type: type) -> dict[Any, Any]:
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
