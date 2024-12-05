from abc import\
    abstractclassmethod,\
    abstractmethod,\
    ABC
from typing import\
    Generic,\
    TypeVar,\
    Generator,\
    Union,\
    Any,\
    get_args,\
    Optional
from .builtin import\
    builtin_instance
from .composite import\
    composite
from .table import\
    table
from .enums import\
    enums
from psycopg import \
    AsyncConnection,\
    AsyncTransaction,\
    AsyncCursor
from collections.abc import\
    AsyncIterator
from psycopg.rows import\
    dict_row
from contextlib import\
    asynccontextmanager
from pydantic import\
    BaseModel


K = TypeVar("K")
V = Union[composite, table, enums, builtin_instance]


class pg_function_builtin(type):
    def __new__(
        cls, clsname: str, clsbases: tuple[type],
        clsdict: dict[str, Any], **kwargs
    ) -> type:
        if len(clsbases) > 1:
            raise TypeError(f'Class {cls} doesnt allow multiple bases')
        return super().__new__(cls, clsname, clsbases, clsdict)


class pg_cursor_wrapper(ABC):
    @asynccontextmanager
    @abstractmethod
    async def cursor(self) -> AsyncIterator[AsyncCursor]:
        pass


class pg_connection_wrapper(pg_cursor_wrapper):
    def __init__(self, conn: AsyncConnection) -> None:
        self._conn = conn

    @asynccontextmanager
    async def cursor(self) -> AsyncIterator[AsyncCursor]:
        cursor: AsyncCursor = self._conn.cursor(row_factory=dict_row)
        transaction: AsyncTransaction = cursor.transaction()
        yield cursor
        transaction.close()
        cursor.close()


class pg_cursor_wrapper(pg_cursor_wrapper):
    def __init__(self, cursor: AsyncCursor) -> None:
        self._cursor = cursor
        assert cursor.row_factory == dict_row

    @asynccontextmanager
    async def cursor(self) -> AsyncIterator[AsyncCursor]:
        yield self._cursor


class pg_function(Generic[K], metaclass=pg_function_builtin):
    def __init__(self, op_wrapper: pg_cursor_wrapper) -> None:
        self._op_wrapper = op_wrapper

    @asynccontextmanager
    async def _call(self, prefix: str, params: dict[str, V]) -> AsyncIterator[AsyncCursor]:
        error: Optional[Exception] = None
        with self._op_wrapper.cursor() as cursor:
            try:
                query_params: list[str] = [f'{param} := %({param})s' for param in params]
                await cursor.execute(f'{prefix} {self.__name__}({", ".join(query_params)})', params)
                yield cursor
            except Exception as e:
                error = e
        if error is not None:
            raise error

    def convert(self, result: Any | dict[str, Any]) -> K:
        base_type: type[K] = get_args(self.__orig_bases__)[0]
        if isinstance(result, dict):
            if not issubclass(base_type, BaseModel):
                raise ValueError(f'Cant convert value {result} to type argument {base_type}')
            return base_type(**result)
        else:
            return base_type(result)


class pg_single_result_function(pg_function[K]):
    async def __call__(self, **kwargs: dict[str, V]) -> Optional[K]:
        result: Optional[K] = None
        with self._call('SELECT', kwargs) as cursor:
            result = cursor.fetchone()
        return result


class pg_set_returning_function(pg_function[K]):
    async def __call__(self, **kwargs: dict[str, V]) -> AsyncIterator[Optional[K]]:
        with self._call('SELECT * FROM', kwargs) as cursor:
            for result in cursor.fetchall():
                yield result


class pg_execute_function(pg_function[None]):
    async def __call__(self, **kwargs: dict[str, V]) -> None:
        with self._call('PERFORM', kwargs) as cursor:
            pass
        return None
