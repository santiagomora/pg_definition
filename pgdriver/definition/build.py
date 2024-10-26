from datetime import\
    datetime,\
    time,\
    date
from numbers import\
    Number
from .base.composite import\
    pg_composite
from .base.table import\
    pg_table
from .base.enums import\
    pg_enum
from .base.builtin import\
    pg_builtin
from .base.common.meta import\
    pg_check,\
    pg_comment,\
    pg_default_value
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


def with_pg_default_value(value: pg_default_value):

    def _add_to_definition(target: type):
        # esto va a cambiar, no se deberia poder acceder a la definicion directamente
        # __pg_definition deberia devolver una copia siempre
        # no puede usarse con pg_table o pg_composite
        assert type(target) == pg_builtin or issubclass(target, pg_composite)
        definition = getattr(target, '__pg_definition')()
        assert definition['default_value'] is None
        definition['default_value'] = value
        return target

    return _add_to_definition


def with_pg_comment(comment: pg_comment):

    def _add_to_definition(target: type):
        # esto va a cambiar, no se deberia poder acceder a la definicion directamente
        # esto deberia devolver una copia siempre
        definition = getattr(target, '__pg_definition')()
        assert definition['comment'] is None
        definition['comment'] = comment
        return target

    return _add_to_definition


def with_pg_check(check: pg_check):

    def _add_to_definition(target: type):
        # esto va a cambiar, no se deberia poder acceder a la definicion directamente
        # esto deberia devolver una copia siempre
        assert type(target) == pg_builtin
        definition = getattr(target, '__pg_definition')()
        check.check_valid_constraint_definition(target)
        parent_definition = getattr(target.__bases__[0], '__pg_definition')()
        if 'check' in parent_definition and parent_definition['check'] is not None:
            check.merge(parent_definition['check'])
        definition['check'] = check
        return target

    return _add_to_definition


__all__ = {
    'pg_composite':             pg_composite,
    'pg_table':                 pg_table,
    'pg_enum':                  pg_enum,
    'pg_int':                   pg_int,
    'pg_bigint':                pg_bigint,
    'pg_smallint':              pg_smallint,
    'pg_text':                  pg_text,
    'pg_double':                pg_double,
    'pg_bytea':                 pg_bytea,
    'pg_timestamp':             pg_timestamp,
    'pg_timestamptz':           pg_timestamptz,
    'pg_time':                  pg_time,
    'pg_timetz':                pg_timetz,
    'pg_date':                  pg_date,
    'pg_boolean':               pg_boolean,
    'pg_bigint_sequence':       pg_bigint_sequence,
    'pg_int_sequence':          pg_int_sequence,
    'pg_default_value':         pg_default_value,
    'pg_check':                 pg_check,
    'pg_comment':               pg_comment,
    'pg_smallint_sequence':     pg_smallint_sequence,
    'with_pg_max_value':        with_pg_max_value,
    'with_pg_default_value':    with_pg_default_value,
    'with_pg_comment':          with_pg_comment,
    'with_pg_check':            with_pg_check,
    'with_pg_min_value':        with_pg_min_value}
