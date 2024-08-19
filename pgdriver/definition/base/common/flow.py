from abc import\
    abstractmethod
from typing import\
    Any,\
    Optional,\
    ContextManager
from typing_extensions import\
    Self
from enum import\
    Enum,\
    auto
import pprint
# from heapq import\
#     heappush,\
#     heappop
from contextlib import\
    contextmanager
# from pgdriver.definition.flows import\
#     DefinitionFlowRegistry
# from pgdriver.definition.flows.table import\
#     pg_table_definition_flow
# from pgdriver.definition.flows.composite import\
#     pg_composite_definition_flow
# from pgdriver.definition.flows.domain import\
#     pg_domain_definition_flow
# from pgdriver.definition.flows.enum import\
#     pg_enum_definition_flow
# from pgdriver.definition.flows.sequence import\
#     pg_sequence_definition_flow
# from pgdriver.definition.flows import\
#     FlowAccumulator


class FlowNodeException(Exception):
    def __init__(self, name, error_list):
        Exception.__init__(self, ', '.join(error_list))
        self.error_list = error_list
        self.component_name = name


class FlowEndException(Exception):
    def __init__(self, errors: dict[str, dict[str, FlowNodeException]]):
        Exception.__init__(self, pprint.pformat(errors))
        self._errors = errors

    def get_error(self, flow_name: str, component_name: str) -> Optional[FlowNodeException]:
        if flow_name in self._errors:
            if component_name in self._errors[flow_name]:
                return self._errors[flow_name][component_name]
        return None


class FlowAccumulatorErrorsPolicy(Enum):
    LOG_INFO = auto()
    END_FLOW = auto()


class HandlesWorkPath:
    def __init__(self):
        self._work_path = ''

    @contextmanager
    def at_work_path(self, name: str) -> ContextManager[Self]:
        old_path: str = self._work_path
        self._work_path = name if self._work_path == '' else f'{self._work_path}.{name}'
        yield self
        self._work_path = old_path


class FlowAccumulator(HandlesWorkPath):
    def __init__(self, on_type: type) -> None:
        HandlesWorkPath.__init__(self)
        self._definition = dict[Any, Any]()
        self._errors: dict[str, dict[str, str]] = dict()
        self._on_type = on_type

    @property
    def errors(self) -> dict[str, Any]:
        return self._errors

    def clear(self) -> None:
        self._definition.clear()
        self._errors.clear()

    def has_errors(self):
        return len(self._errors.keys()) != 0

    def get_definition(self, name: Optional[str] = None,
                       abspath: Optional[str] = None) -> Optional[Any]:
        dic: dict[str, Any] = self._definition
        if name is None:
            return dic
        if abspath is None:
            return None if name not in dic else dic[name]
        path: list[str] = abspath.split('.')
        for ix in range(0, len(path)):
            at: str = path[ix]
            if at not in dic:
                return None
            if not isinstance(dic[at],  dict):
                err_path: str = '.'.join(path[0:ix]) + at
                raise Exception(f'Accessing invalid level at definition flow: {err_path}')
            dic = dic[at]
        return None if name not in dic else dic[name]

    def add_definition(self, name: str, definition: Any) -> Self:
        dic: dict[str, Any] = self._definition
        if self._work_path == '':
            dic[name] = definition
            return self
        path: list[str] = self._work_path.split('.')
        for ix in range(0, len(path)):
            at: str = path[ix]
            if at in dic:
                if type(dic[at]) != dict:
                    err_path: str = '.'.join(path[0:ix]) + at
                    raise Exception(f'Invalid level detected at definition flow: {err_path}')
            else:
                dic[at] = {}
            dic = dic[at]
        if name in dic:
            raise Exception('Cant modify existing key')
        dic[name] = definition
        return self

    def add_exception(self, flow_name: str, exception: FlowNodeException) -> Self:
        flow_errors = self._errors.get(flow_name, {})
        flow_errors[exception.component_name] = exception
        self._errors[flow_name] = flow_errors
        return self


class DefinitionFlowNode:
    def __init__(self, n_choices: int, name: str) -> None:
        self.accumulator_path = ''
        self.name = name
        self._n_choices = n_choices
        self._accumulator_errors_policy = FlowAccumulatorErrorsPolicy.LOG_INFO
        self._nodes = dict[str, DefinitionFlowNode]()
        self._registered_node_names = set[str]()

    def critical(self) -> Self:
        self._accumulator_errors_policy = FlowAccumulatorErrorsPolicy.END_FLOW
        return self

    def initialize(self, accumulator: FlowAccumulator) -> None:
        if not accumulator.has_errors():
            return
        if self._accumulator_errors_policy == FlowAccumulatorErrorsPolicy.END_FLOW:
            raise FlowEndException(accumulator.errors)

    def get_dependencies(self) -> tuple[str]:
        return tuple()

    def _add_node(self, other: 'DefinitionFlowNode') -> None:
        if len(self._nodes.keys()) > self._n_choices:
            raise Exception(f'Definition node {self.name} maximum size reached.')
        if other.name in self._nodes:
            raise Exception(f'Definition Node {other.name} already defined in {self.name}')
        self._nodes[other.name] = other

    def print_tree(self, level: int = 0) -> None:
        indent: str = '  '*level
        critical = ''
        if self._accumulator_errors_policy == FlowAccumulatorErrorsPolicy.END_FLOW:
            critical = ' (critical)'
        print(f'{indent}{self.name}{critical}')
        for node in self._nodes:
            self._nodes[node].print_tree(level+1)

    @abstractmethod
    def execute(self, on_type: type, accumulator: FlowAccumulator) -> None:
        pass

    @abstractmethod
    def set_next(self, other: 'DefinitionFlowNode') -> Self:
        pass

    @abstractmethod
    def get_next(self, accumulator: FlowAccumulator) -> Optional['DefinitionFlowNode']:
        """
        Next node to execute will be decided taking into account variables
        inside the accumulator
        """
        pass


class SingleChoiceDefinitionFlowNode(DefinitionFlowNode):
    def __init__(self,
                 name: str) -> None:
        super().__init__(1, name)

    def set_next(self, other: DefinitionFlowNode) -> DefinitionFlowNode:
        self._add_node(other)
        return other

    def get_next(self, accumulator: FlowAccumulator) -> Optional[DefinitionFlowNode]:
        if len(self._nodes) <= 0:
            return None
        return list(self._nodes.values())[0]


class MultipleChoiceDefinitionFlowNode(DefinitionFlowNode):
    def set_next(self, other: DefinitionFlowNode) -> DefinitionFlowNode:
        self._add_node(other)
        return self


class RootDefinitionFlowNode(SingleChoiceDefinitionFlowNode):
    def execute(self, on_type: type, accumulator: FlowAccumulator) -> None:
        node: DefinitionFlowNode = self.get_next(accumulator)
        executed: set[str] = set[str]()
        while node is not None:
            last_accumulator_path: str = node.accumulator_path
            with accumulator.at_work_path(last_accumulator_path) as acc:
                while node is not None and\
                      last_accumulator_path == node.accumulator_path:
                    try:
                        node.initialize(acc)
                        dependencies: set[str] = set(node.get_dependencies())
                        if not dependencies.issubset(executed):
                            raise RuntimeError(f'Dependencies not met for node {node.name}')
                        executed.add(node.name)
                        node.execute(on_type, acc)
                    except FlowNodeException as e:
                        accumulator.add_exception(self.name, e)
                    except FlowEndException as e:
                        raise e
                    except RuntimeError as e:
                        raise e
                    node = node.get_next(acc)


class DefinitionFlowNodeFactory(HandlesWorkPath):
    def get_definition_node(self, cls: type[DefinitionFlowNode], *args,
                            **kwargs) -> DefinitionFlowNode:
        instance = cls(*args, **kwargs)
        instance.accumulator_path = self._work_path
        return instance


def execute_definition_flow(on_type: type, root: RootDefinitionFlowNode) -> dict[str, Any]:
    accumulator: FlowAccumulator = FlowAccumulator(on_type)
    root.execute(on_type, accumulator)
    final: dict[str, Any] = accumulator.get_definition('final')

    @classmethod
    def __pg_definition(cls) -> dict[str, Any]:
        return final
    setattr(on_type, '__pg_definition', __pg_definition)
