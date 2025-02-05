from typing import\
    Generic,\
    TypeVar,\
    Any,\
    get_args,\
    Optional,\
    Callable
from ..common.flow import\
    FlowAccumulator,\
    RootDefinitionFlowNode,\
    SingleChoiceDefinitionFlowNode,\
    DefinitionFlowBuilder,\
    execute_definition_flow
from .comment import\
    add_comment


__all__ = ['function']


_function_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('function-definition-flow')
function_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(_function_definition_flow_root)


T = TypeVar("T")


class _function(type, Generic[T]):
    def __new__(
        cls, clsname, clsbases, namespace, *, function: Callable[[Any, ...], T]
    ) -> type:
        def __new__(cls, *args) -> T:
            return function(*args)
        rettype = super().__new__(
            cls, clsname, clsbases, namespace | {'__new__': __new__}
        )
        execute_definition_flow(rettype, _function_definition_flow_root)
        return rettype


class function(Generic[T], metaclass=_function[T], function=None):
    class add_comment(add_comment):
        pass


class _FunctionExtractReturnTypeNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('function-extract-return-type-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        # might be a function that discards the result
        # rettype: Optional[type] = None
        # if hasattr(target.__class__, '__orig_bases__'):
        #     rettype = get_args(target.__orig_bases__[0])[0]
            # print(get_args(target.__orig_bases__[0])[0])
            # is_subclass: bool = any([issubclass(rettype, cls) for cls in (enum, builtin, composite, table, )])
            # if not is_subclass and not isinstance(rettype, builtin):
                # raise NodeException(self.name, [f'Function return type must be a valid pg type, received {rettype}'])
        accumulator.add_definition('return_type', get_args(target.__orig_bases__[0])[0])


class _FunctionStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('function-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Optional[str]] = dict()
        definition['schema'] = None
        definition['type'] = target
        definition['comment'] = None
        definition['kind'] = 'function'
        definition['return_type'] = accumulator.get_definition('return_type', 'extraction')
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('function-extract-return-type-node', )


function_flow_builder\
    .at_work_path('extraction')\
    .add_node(_FunctionExtractReturnTypeNode)\
    .at_work_path('')\
    .add_node(_FunctionStoreFinalDefinitionNode).critical()
