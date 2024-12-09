from .builtin import\
    integer,\
    bigint,\
    smallint,\
    real,\
    text,\
    char,\
    double,\
    byte,\
    timestamptz,\
    timetz,\
    date,\
    builtin,\
    boolean
from ..extension import\
    Extension
from typing import\
    Generator


__all__ = ['base_extension']


class _BaseExtension(Extension):
    def types(self) -> Generator[type[builtin], None, None]:
        yield integer
        yield bigint
        yield smallint
        yield real
        yield text
        yield char
        yield double
        yield byte
        yield timestamptz
        yield timetz
        yield date
        yield boolean

    def get_type_psycopg_name(self, tp: type) -> str:
        if tp in (byte, char):
            return '"char"'
        elif tp == double:
            return 'double precision'
        return tp.__name__


base_extension: _BaseExtension = _BaseExtension('pg_catalog')
