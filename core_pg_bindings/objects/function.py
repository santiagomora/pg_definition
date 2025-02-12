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
from .comment import\
    add_comment
import inspect



__all__ = ['function', 'FunctionSQLDefinition']


_function_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('function-definition-flow')
function_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(_function_definition_flow_root)


T = TypeVar("T")


class FunctionSQLDefinition(dict[str, str]):
    def __init__(self, *, schema_name: str, names: Optional[tuple[str, ...]] = None):
        self.names = names
        self.load: bool = False
        self.schema_name = schema_name

    def _load_functions_from_file(
        self, fns: TextIO
    ) -> dict[str, list[str]]:
        schema = self.schema_name
        names = self.names
        res: dict[str, str] = {}
        buf, func_name = [], ''
        stack: list[str] = []
        params_stack: list[str] = []
        create_re = r'\s*CREATE\s+OR\s+REPLACE\s+FUNCTION\s*'
        read_func: bool = True
        read_func_name: bool = False
        params_str: str = ''
        for line in fns:
            buf.append(line.rstrip())
            if re.match(create_re, line) is not None:
                func_name = re.sub(create_re, '', line)
                func_name = re.sub(r'\s*\(.*\n', '', func_name)
                buf[0] = buf[0].replace(func_name, f'{schema}.{func_name}')
                read_func = func_name in (names if names is not None else (func_name, ))
                read_func_name = read_func
                if read_func:
                    stack.append(func_name)
            if read_func_name:
                if '(' in line:
                    if ')' in line:
                        params_str = re.match(r'\(.*\)').group(0)
                    else:
                        params_stack.append(re.match(r'\(.*').group(0))
                elif ')' in line:
                    if len(params_stack) > 0:
                        params_stack.append(re.match(r'.*\)').group(0))
                    params_str = ''.join(params_stack)
                    read_func_name = False
                    params_stack = []
                else:
                    params_stack.append(line.rstrip('\n'))
            if not read_func:
                buf = []
                continue
            if '$$' in line:
                if len(stack) == 1:
                    # the function started
                    stack.append('$$')
                elif stack[-1] == '$$':
                    # the function finished
                    stack.pop()
                else:
                    raise Exception(f'function doesnt exist: {stack}')
            if ';' in line and len(stack) == 1:
                name: str = stack.pop()
                fn = "\n".join(buf).strip()
                if name not in res:
                    self[name] = {params_str: fn}
                else:
                    # raise Exception('Only one function overload allowed.')
                    if params_str not in self[name]:
                        self[name][params_str]
                    else:
                        raise Exception(f'Invalid function definition "{read_func}", overload "{params_str}" declared more than once')
                buf = []

    def read(self, file_: TextIO) -> None:
        assert not self.load
        self._load_functions_from_file(file_)


class _function(type, Generic[T]):
    def __new__(
        cls, clsname: str, clsbases: tuple[type],
        clsdict: dict[str, Any], *, defined_in: Optional[FunctionSQLDefinition]
    ) -> type:
        rettype = super().__new__(
            cls, clsname, clsbases, clsdict
        )
        execute_definition_flow(rettype, _function_definition_flow_root)
        rettype._postgres_definition['definition'] = defined_in[rettype.__name__]
        return rettype


class function(
    Generic[T], metaclass=_function[T], defined_in=None
):
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
        definition['schema'] = inspect.getmodule(target)
        definition['definition'] = None
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
