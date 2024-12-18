from .base.extension import\
    Extension
from typing import\
    Generator
from .definition.builtin import\
    builtin
from ._schema import\
    pg_catalog


__all__ = ['base_extension']


class _BaseExtension(Extension):
    def types(self) -> Generator[type[builtin], None, None]:
        yield self.schema.int4
        yield self.schema.int8
        yield self.schema.int2
        yield self.schema.float4
        yield self.schema.text
        yield self.schema.char
        yield self.schema.float8
        yield self.schema.bytea
        yield self.schema.timestamptz
        yield self.schema.timetz
        yield self.schema.date
        yield self.schema.bool

    def get_type_psycopg_name(self, tp: type) -> str:
        if tp in (pg_catalog.char, ):
            return '"char"'
        return tp.__name__


base_extension: _BaseExtension = _BaseExtension(pg_catalog)
