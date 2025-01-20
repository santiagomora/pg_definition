# from typing import\
#     Generic,\
#     TypeVar,\
#     Union,\
#     Any,\
#     get_args,\
#     Optional
# from .builtin import\
#     builtin
# from .composite import\
#     composite
# from .table import\
#     table
# from .enums import\
#     enum
# from psycopg import \
#     AsyncCursor
# from ..common.flow import\
#     FlowAccumulator,\
#     NodeException,\
#     RootDefinitionFlowNode,\
#     SingleChoiceDefinitionFlowNode,\
#     DefinitionFlowBuilder,\
#     execute_definition_flow
# import pg_definition.types.cpp.wrapper as bw
# 
# 
# __all__ = ['function']
# 
# 
# _function_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('function-definition-flow')
# function_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(_function_definition_flow_root)
# 
# 
# class function(type(bw.base)):
#     def __new__(
#         cls, clsname: str, clsbases: tuple[type],
#         clsdict: dict[str, Any], **kwargs
#     ) -> type:
#         if len(clsbases) > 1:
#             raise TypeError(f'Class {cls} doesnt allow multiple bases')
#         rettype: type = super().__new__(cls, clsname, clsbases, clsdict)
#         execute_definition_flow(rettype, _function_definition_flow_root)
#         return rettype@classmethod
# 
#     def as_sql_query(cls, prefix: str, params: dict[str, Any]) -> str:
#         query_params: list[str] = [f'{param} := %({param})s' for param in params]
#         schema: str = getattr(cls, '__pg_definition')()['schema'].__name__
#         return f'{prefix} {schema}.{cls.__name__}({", ".join(query_params)})'
# 
#     async def _execute(self, prefix: str, cursor: AsyncCursor, params: dict[str, Any]) -> AsyncCursor:
#         await cursor.execute(self.as_sql_query(prefix, params), params)
#         return cursor
# 
#     def _validate_arguments(self, kwargs: dict[str, Any], instance: 'function') -> dict[str, Any]:
#         definition: dict[str, Any] = getattr(self, '__pg_definition')()
#         validated: Optional[function] = None
#         for overload in definition['overloads']:
#             try:
#                 validated = overload.__pydantic_validator__.\
#                     validate_python(kwargs, self_instance=instance)
#                 break
#             except Exception:
#                 validated = None
#         if validated is None and len(definition['overloads']) > 0:
#             raise ValueError(f'Didnt find suitable overload to execute function "{cls.__name__}"')
#         return {name: getattr(validated, name) for name in kwargs}
# 
# 
# class _FunctionExtractReturnTypeNode(SingleChoiceDefinitionFlowNode):
#     def __init__(self):
#         super().__init__('function-extract-return-type-node')
# 
#     def execute(self, target: type, accumulator: FlowAccumulator) -> None:
#         # might be a function that discards the result
#         rettype: Optional[type] = None
#         if hasattr(target, '__orig_bases__'):
#             rettype = get_args(target.__orig_bases__[0])[0]
#             is_subclass: bool = any([issubclass(rettype, cls) for cls in (enum, builtin, composite, table, )])
#             if not is_subclass and not isinstance(rettype, builtin):
#                 raise NodeException(self.name, [f'Function return type must be a valid pg type, received {rettype}'])
#         accumulator.add_definition('return_type', rettype)
# 
# 
# class _FunctionStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
#     def __init__(self):
#         super().__init__('function-store-final-definition-node')
# 
#     def execute(self, target: type, accumulator: FlowAccumulator) -> None:
#         definition: dict[str, Optional[str]] = dict()
#         definition['schema'] = None
#         definition['type'] = target
#         definition['comment'] = None
#         definition['kind'] = 'function'
#         definition['return_type'] = accumulator.get_definition('return_type', 'extraction')
#         accumulator.add_definition('final', definition)
# 
#     def get_dependencies(self) -> tuple[str]:
#         return ('function-extract-return-type-node', )
# 
# 
# function_flow_builder\
#     .at_work_path('extraction')\
#     .add_node(_FunctionExtractReturnTypeNode)\
#     .at_work_path('')\
#     .add_node(_FunctionStoreFinalDefinitionNode).critical()
