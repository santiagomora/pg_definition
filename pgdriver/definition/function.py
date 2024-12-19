from typing import\
    Generic,\
    TypeVar,\
    Union,\
    Any,\
    get_args,\
    Optional
from .builtin import\
    builtin_instance,\
    builtin
from .composite import\
    composite
from .table import\
    table
from .enums import\
    enums
from psycopg import \
    AsyncCursor
from collections.abc import\
    AsyncIterator
from pydantic import\
    create_model
from .common.flow import\
    FlowAccumulator,\
    NodeException,\
    RootDefinitionFlowNode,\
    SingleChoiceDefinitionFlowNode,\
    DefinitionFlowBuilder,\
    execute_definition_flow
from .common.inspection import\
    is_pg_type
import os


__all__ = ['single_result_function', 'discard_result_function', 'single_result_function']


V = Union[composite, table, enums, builtin_instance]
K = TypeVar("K", composite, table, enums, builtin_instance)


_function_definition_flow_root: RootDefinitionFlowNode = RootDefinitionFlowNode('function-definition-flow')
function_flow_builder: DefinitionFlowBuilder = DefinitionFlowBuilder(_function_definition_flow_root)


class register_overload:
    def __init__(self, members: dict[str, type[V]]):
        errors: list[str] = []
        for memb in members:
            errors += is_pg_type(
                memb, members[memb], [enums, builtin, composite, table],
                [builtin]
            )
        if len(errors) > 0:
            raise TypeError('\n'.join(errors))
        self.members = members

    def __call__(self, target: type) -> type:
        assert issubclass(target, function)
        definition = getattr(target, '__pg_definition')()
        definition['overloads'].append(
            create_model(
                f'{target.__name__}_ArgumentModel',
                **{memb: (self.members[memb], ...) for memb in self.members}
            ))
        return target


class function_builtin(type):
    def __new__(
        cls, clsname: str, clsbases: tuple[type],
        clsdict: dict[str, Any], **kwargs
    ) -> type:
        is_base = clsname in ('function_builtin', 'discard_result_function', 'set_returning_function', 'single_result_function', 'function')
        if len(clsbases) > 1 and not is_base:
            raise TypeError(f'Class {cls} doesnt allow multiple bases')
        rettype: type = super().__new__(cls, clsname, clsbases, clsdict)
        if not is_base:
            execute_definition_flow(rettype, _function_definition_flow_root)
        return rettype


class _FunctionExtractReturnTypeNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('function-extract-return-type-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        # might be a function that discards the result
        rettype: Optional[type] = None
        if hasattr(target, '__orig_bases__'):
            rettype = get_args(target.__orig_bases__[0])[0]
            is_subclass: bool = any([issubclass(rettype, cls) for cls in (enums, builtin, composite, table, )])
            if not is_subclass and not isinstance(rettype, builtin):
                raise NodeException(self.name, [f'Function return type must be a valid pg type, received {rettype}'])
        accumulator.add_definition('return_type', rettype)


class _FunctionStoreFinalDefinitionNode(SingleChoiceDefinitionFlowNode):
    def __init__(self):
        super().__init__('function-store-final-definition-node')

    def execute(self, target: type, accumulator: FlowAccumulator) -> None:
        definition: dict[str, Optional[str]] = dict()
        definition['schema'] = None
        definition['type'] = target
        definition['comment'] = None
        definition['kind'] = 'function'
        definition['overloads'] = []
        definition['return_type'] = accumulator.get_definition('return_type', 'extraction')
        accumulator.add_definition('final', definition)

    def get_dependencies(self) -> tuple[str]:
        return ('function-extract-return-type-node', )


function_flow_builder\
    .at_work_path('extraction')\
    .add_node(_FunctionExtractReturnTypeNode)\
    .at_work_path('')\
    .add_node(_FunctionStoreFinalDefinitionNode).critical()


class function(metaclass=function_builtin):
    @classmethod
    def as_sql_query(cls, prefix: str, params: dict[str, Any]) -> str:
        query_params: list[str] = [f'{param} := %({param})s' for param in params]
        schema: str = getattr(cls, '__pg_definition')()['schema'].__name__
        return f'{prefix} {schema}.{cls.__name__}({", ".join(query_params)})'

    @classmethod
    async def _execute(cls, prefix: str, cursor: AsyncCursor, params: dict[str, V]) -> AsyncCursor:
        await cursor.execute(cls.as_sql_query(prefix, params), params)
        return cursor

    @classmethod
    def _validate_arguments(cls, kwargs: dict[str, Any], instance: 'function') -> dict[str, V]:
        definition: dict[str, Any] = getattr(cls, '__pg_definition')()
        validated: Optional[function] = None
        for overload in definition['overloads']:
            try:
                validated = overload.__pydantic_validator__.\
                    validate_python(kwargs, self_instance=instance)
                break
            except Exception:
                validated = None
        if validated is None and len(definition['overloads']) > 0:
            raise ValueError(f'Didnt find suitable overload to execute function "{cls.__name__}"')
        return {name: getattr(validated, name) for name in kwargs}


class single_result_function(function, Generic[K]):
    async def __new__(cls, cursor: AsyncCursor, **kwargs: dict[str, Any]) -> Optional[K]:
        instance = super(function, cls).__new__(cls)
        kwargs = cls._validate_arguments(kwargs, instance)
        result: Optional[K] = None
        cursor: AsyncCursor = await cls._execute('SELECT', cursor, kwargs)
        result: tuple[K, ...] = await cursor.fetchone()
        return result[0]


class set_returning_function(function, Generic[K]):
    async def __new__(cls, cursor: AsyncCursor, **kwargs: dict[str, V]) -> AsyncIterator[Optional[K]]:
        instance = super(function, cls).__new__(cls)
        kwargs = cls._validate_arguments(kwargs, instance)
        cursor: AsyncCursor = await cls._execute('SELECT', cursor, kwargs)
        for result in await cursor.fetchall():
            yield result[0]


class discard_result_function(function):
    async def __new__(cls, cursor: AsyncCursor, **kwargs: dict[str, V]) -> None:
        instance = super(function, cls).__new__(cls)
        kwargs = cls._validate_arguments(kwargs, instance)
        await cls._execute('PERFORM', cursor, kwargs)
