from abc import ABC, abstractmethod
from typing import Any, Optional, Iterator
from .types.base import pg_type
from psycopg import AsyncConnection


class Operation(ABC):
    params: Optional[dict[str, pg_type]]

    @abstractmethod
    def as_text(self, connection: AsyncConnection[tuple[Any, ...]]) -> tuple[str, Optional[dict[str, pg_type]]]:
        pass


class ClassRegistry(ABC):
    @abstractmethod
    def composite_registry(self) -> Iterator[pg_type]:
        pass

    @abstractmethod
    def class_registry(self) -> Iterator[pg_type]:
        pass

    @abstractmethod
    def enum_registry(self) -> Iterator[pg_type]:
        pass

    @abstractmethod
    def type_registry(self) -> Iterator[pg_type]:
        pass

