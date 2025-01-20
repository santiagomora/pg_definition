import base_types as bt
from pydantic_core import\
    core_schema
from pydantic import\
    GetCoreSchemaHandler


__all__ = ['check']


class check:
    def __init__(
        self, name: str, predicate: bt.LogicOperand
    ) -> None:
        self.predicate = predicate
        self.name = name
        predicate.parent = self

    def __repr__(self) -> str:
        return f'check(name={self.name}, predicate={repr(self.predicate)})'

    def __str__(self) -> str:
        return f'({str(self.predicate)})'

    def __get_pydantic_core_schema__(
        self, source: type, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return getattr(self.predicate, '__get_pydantic_core_schema__')(
            source, handler
        )
