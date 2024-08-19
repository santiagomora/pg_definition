from datetime import\
    datetime,\
    time,\
    date
from numbers import\
    Number
from .base.composite import\
    pg_composite,\
    pg_composite_meta
from .base.table import\
    pg_table,\
    pg_table_meta
from .base.enums import\
    pg_enum
from .base.sequence import\
    pg_bigint_sequence,\
    pg_int_sequence,\
    pg_smallint_sequence,\
    with_pg_max_value,\
    with_pg_min_value
from .base.builtin import\
    pg_int,\
    pg_bigint,\
    pg_smallint,\
    pg_float,\
    pg_text,\
    pg_double,\
    pg_bytea,\
    pg_timestamp,\
    pg_timestamptz,\
    pg_time,\
    pg_timetz,\
    pg_date,\
    pg_boolean
from .base.common.meta import\
    pg_check as _pg_check


_pg_check.type_compatibility.register(pg_bigint, Number)
_pg_check.type_compatibility.register(pg_int, Number)
_pg_check.type_compatibility.register(pg_smallint, Number)
_pg_check.type_compatibility.register(pg_double, Number)
_pg_check.type_compatibility.register(pg_float, Number)
_pg_check.type_compatibility.register(pg_time, time)
_pg_check.type_compatibility.register(pg_timetz, time)
_pg_check.type_compatibility.register(pg_date, date)
_pg_check.type_compatibility.register(pg_text, str)
_pg_check.type_compatibility.register(pg_timestamp, datetime)
_pg_check.type_compatibility.register(pg_timestamptz, datetime)
_pg_check.type_compatibility.register(pg_boolean, bool)
_pg_check.type_compatibility.register(pg_composite, pg_composite)


__all__ = {
    'pg_composite':         pg_composite,
    'pg_composite_meta':    pg_composite_meta,
    'pg_table':             pg_table,
    'pg_table_meta':        pg_table_meta,
    'pg_enum':              pg_enum,
    'pg_int':               pg_int,
    'pg_bigint':            pg_bigint,
    'pg_smallint':          pg_smallint,
    'pg_text':              pg_text,
    'pg_double':            pg_double,
    'pg_bytea':             pg_bytea,
    'pg_timestamp':         pg_timestamp,
    'pg_timestamptz':       pg_timestamptz,
    'pg_time':              pg_time,
    'pg_timetz':            pg_timetz,
    'pg_date':              pg_date,
    'pg_boolean':           pg_boolean,
    'pg_bigint_sequence':   pg_bigint_sequence,
    'pg_int_sequence':      pg_int_sequence,
    'pg_smallint_sequence': pg_smallint_sequence,
    'with_pg_max_value':    with_pg_max_value,
    'with_pg_min_value':    with_pg_min_value}
