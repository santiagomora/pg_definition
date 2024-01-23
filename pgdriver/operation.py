from psycopg import AsyncConnection
from typing import Any, Optional
from typing_extensions import Self
from .types.base import pg_type
from psycopg import sql
from .exception import PGOperationNotBuiltError
from .abc import Operation


class Proc(Operation):
    def __init__(self, procname: str) -> None:
        self._procname: str = procname
        self._unnest: bool = False
        self.params: Optional[dict[str, pg_type]] = None

    def unnest(self) -> Self:
        self._unnest = True
        return self

    def as_text(self, connection: AsyncConnection[tuple[Any, ...]]) -> tuple[str, Optional[dict[str, pg_type]]]:
        argbase: str = '()'
        if self.params is not None:
            argbase = '({})'.format(', '.join([
                f'{name} := {sql.Placeholder(name).as_string(connection)}'
                for name in self.params]))
        selbase: str = 'SELECT * FROM' if self._unnest else 'SELECT'
        query: sql.Composed = sql.SQL(f'{selbase} {self._procname}{argbase}')\
            .format(self.params)
        return query.as_string(connection), self.params


class Query(Operation):
    def __init__(self, query: str) -> None:
        self._query = sql.SQL(query)
        self.params: Optional[dict[str, pg_type]] = None

    def as_text(self, connection: AsyncConnection[tuple[Any, ...]]) -> tuple[str, Optional[dict[str, pg_type]]]:
        return self._query.as_string(connection), self.params


class Builder:
    def __init__(self) -> None:
        self._operation: Optional[Operation] = None

    def call_function(self, name: str) -> Self:
        self._operation = Proc(name)
        return self

    def query(self, querystr: str) -> Self:
        self._operation = Query(querystr)
        return self

    def with_params(self, params: dict[str, pg_type]) -> Self:
        if self._operation is None:
            raise PGOperationNotBuiltError
        self._operation.params = params
        return self

    def done(self) -> Operation:
        if self._operation is None:
            raise PGOperationNotBuiltError
        operation = self._operation
        self._operation = None
        return operation
