from typing import\
    Generic,\
    TypeVar,\
    Any,\
    get_args,\
    Optional,\
    Callable,\
    TextIO
from ..common.flow import\
    FlowAccumulator,\
    RootDefinitionFlowNode,\
    SingleChoiceDefinitionFlowNode,\
    DefinitionFlowBuilder,\
    execute_definition_flow
from ..objects.comment import\
    add_comment
import inspect
import os
from ..common.inspection import\
    load_functions_from_file
from typing_extensions import\
    Self
import core_types as ct
from ..common.flow import\
    NodeException
import re


__all__ = ['function']


_function_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('function-definition-flow')
function_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(_function_definition_flow_root)


T = TypeVar("T")


class function(type(ct.ct_pybind_base)):
    class add_comment(add_comment):
        pass

    def __new__(
        cls, clsname: str, clsbases: tuple[type],
        clsdict: dict[str, Any]
    ) -> type:
        rettype = super().__new__(
            cls, clsname, clsbases, clsdict
        )
        execute_definition_flow(rettype, _function_definition_flow_root)
        return rettype


class _FunctionExtractReturnTypeNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('function-extract-overloads-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        if len(target._cpp_overloads) == 0:
            errors.append(f'Empty function definition: "{target}"')
        res: dict[str, str] = {}
        for overload in target._cpp_overloads:
            params = re.search(r'\(.*\)', overload.split("$$")[0], re.DOTALL).group(0)
            params = re.sub(r'((\(\s*)|(\s*\))|\n)', '', params)
            params = re.sub(r'\s+', ' ', params)
            if len(params) > 0:
                params = params.split(', ')
                param_names = [param_tuple_str.split(" ")[0] for param_tuple_str in params]
                param_types = [param_tuple_str.split(" ")[1] for param_tuple_str in params]
                params = ', '.join(param_types)
                ol = {'overload': overload, 'param_names': param_names, 'param_types': param_types}
            else:
                ol = {'overload': overload, 'param_names': None, 'param_types': None}
            if params in res:
                errors.append(f'Duplicated overload : "{params}"')
            else:
                res[params] = ol
        if len(errors) > 0:
            raise NodeException(self.name, errors)
        accumulator.add_definition('overloads', res)


class _FunctionStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('function-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Optional[str]] = dict()
        definition['schema'] = inspect.getmodule(target)
        definition['overloads'] = accumulator.get_definition('overloads', 'extraction')
        definition['type'] = target
        definition['comment'] = None
        definition['kind'] = 'function'
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('function-extract-overloads-node', )


function_flow_builder\
    .at_work_path('extraction')\
    .add_node(_FunctionExtractReturnTypeNode)\
    .at_work_path('')\
    .add_node(_FunctionStoreFinalDefinitionNode).critical()
