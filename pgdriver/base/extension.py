from typing import\
    Generator
from abc import\
    ABC
from .adapter_registry import\
    _AdapterRegistry
from pgdriver.definition.schema import\
    schema


class Extension(ABC):
    def __init__(self, schema: schema):
        self.schema = schema

    def composites(self) -> Generator[type, None, None]:
        yield from ()

    def tables(self) -> Generator[type, None, None]:
        yield from ()

    def enums(self) -> Generator[type, None, None]:
        yield from ()

    def sequences(self) -> Generator[type, None, None]:
        yield from ()

    def functions(self) -> Generator[type, None, None]:
        yield from ()

    def types(self) -> Generator[type, None, None]:
        yield from ()

    def get_type_psycopg_name(self, tp: type) -> str:
        # get type name as it appears in psycopg registry
        return tp.__name__

    def register_types(self, ar: _AdapterRegistry) -> None:
        for composite in self.composites():
            ar.register_composite(composite, self.schema.__name__, self.get_type_psycopg_name(composite))
        for table in self.tables():
            ar.register_composite(table, self.schema.__name__, self.get_type_psycopg_name(table))
        for en in self.enums():
            ar.register_enum(en, self.schema.__name__, self.get_type_psycopg_name(en))
        for tp in self.types():
            ar.register_type(tp, self.schema.__name__, self.get_type_psycopg_name(tp))
