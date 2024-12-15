import pgdriver.definition.builtin as bt
from ..extension import\
    Extension
from typing import\
    Generator


__all__ = ['base_extension']


class _BaseExtension(Extension):
    def types(self) -> Generator[type[bt.builtin], None, None]:
        yield bt.int4
        yield bt.int8
        yield bt.int2
        yield bt.float4
        yield bt.text
        yield bt.char
        yield bt.float8
        yield bt.bytea
        yield bt.timestamptz
        yield bt.timetz
        yield bt.date
        yield bt.bool

    def get_type_psycopg_name(self, tp: type) -> str:
        if tp in (bt.char, ):
            return '"char"'
        return tp.__name__


base_extension: _BaseExtension = _BaseExtension('pg_catalog')
