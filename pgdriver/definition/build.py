from datetime import\
    datetime,\
    time,\
    date
from numbers import\
    Number
from typing import\
    Any,\
    Generic
from .base.composite import\
    pg_composite
from .base.table import\
    pg_table,\
    pg_default_sequence_nextval
from .base.enums import\
    pg_enum
from .base.builtin import\
    pg_builtin
from .base.common.meta import\
    pg_check,\
    LogicOperand,\
    OperandDefinitionContext,\
    pg_comment,\
    literal,\
    pg_default_value
from .base.sequence import\
    pg_bigint_sequence,\
    pg_int_sequence,\
    pg_smallint_sequence,\
    pg_sequence
from .base.builtin import\
    pg_int,\
    pg_bigint,\
    pg_smallint,\
    pg_float,\
    pg_text,\
    pg_char,\
    pg_double,\
    pg_byte,\
    pg_datetime,\
    pg_time,\
    pg_date,\
    pg_boolean


pg_check.type_compatibility.register(pg_bigint, Number)
pg_check.type_compatibility.register(pg_int, Number)
pg_check.type_compatibility.register(pg_smallint, Number)
pg_check.type_compatibility.register(pg_double, Number)
pg_check.type_compatibility.register(pg_float, Number)
pg_check.type_compatibility.register(pg_time, time)
pg_check.type_compatibility.register(pg_date, date)
pg_check.type_compatibility.register(pg_text, str)
pg_check.type_compatibility.register(pg_datetime, datetime)
pg_check.type_compatibility.register(pg_boolean, bool)
pg_check.type_compatibility.register(pg_composite, pg_composite)


__all__ = ['pg_composite', 'pg_table', 'pg_enum', 'pg_int', 'pg_bigint', 'pg_smallint',
           'pg_text', 'pg_double', 'pg_byte', 'pg_char', 'pg_datetime', 'pg_time', 'pg_date',
           'pg_boolean', 'pg_bigint_sequence', 'pg_int_sequence', 'pg_default_value',
           'pg_check', 'pg_comment', 'pg_smallint_sequence', 'with_pg_max_value',
           'with_pg_default_value', 'with_pg_comment', 'with_pg_check', 'with_pg_min_value',
           'pg_default_sequence_nextval', 'with_pg_increment']


def with_pg_default_value(*args, **kwargs):

    def _add_to_definition(target: type):
        # esto va a cambiar, no se deberia poder acceder a la definicion directamente
        # __pg_definition deberia devolver una copia siempre
        # no puede usarse con pg_table o pg_composite
        assert hasattr(target.__bases__[0], '__pg_definition')
        definition = getattr(target, '__pg_definition')()
        assert definition['default_value'] is None
        value: pg_default_value = pg_default_value(*args, **kwargs)
        value.default.propagate_definition(target, None, OperandDefinitionContext.BUILTIN_DOMAIN)
        definition['default_value'] = value
        return target

    return _add_to_definition


def with_pg_comment(comment: str):

    def _add_to_definition(target: type):
        # esto va a cambiar, no se deberia poder acceder a la definicion directamente
        # esto deberia devolver una copia siempre
        definition = getattr(target, '__pg_definition')()
        assert definition['comment'] is None
        assert isinstance(comment, str)
        definition['comment'] = pg_comment(comment)
        return target

    return _add_to_definition


class with_pg_check:
    def __init__(self, name: str,  predicate: LogicOperand) -> None:
        self._check: pg_check = pg_check(name=name, predicate=predicate)

    def __call__(self, target: type):
        definition = getattr(target, '__pg_definition')()
        assert definition['check'] is None
        self._check.predicate.propagate_definition(target, None, OperandDefinitionContext.BUILTIN_DOMAIN)
        definition['check'] = self._check
        return target


class with_pg_max_value:
    def __init__(self, max_value: int):
        self._max_value = max_value

    def __call__(self, wrapped) -> type:
        if not isinstance(wrapped, pg_sequence):
            raise TypeError('Decorated class must be a pg_sequence subclass')
        definition = getattr(wrapped, '__pg_definition')()
        assert 'max_value' in definition
        assert definition['max_value'] is None
        definition['max_value'] = wrapped(self._max_value)
        return wrapped


class with_pg_min_value:
    def __init__(self, min_value: int):
        self._min_value = min_value

    def __call__(self, wrapped) -> type:
        if not isinstance(wrapped, pg_sequence):
            raise TypeError('Decorated class must be a pg_sequence subclass')
        definition = getattr(wrapped, '__pg_definition')()
        assert 'min_value' in definition
        assert definition['min_value'] is None
        definition['min_value'] = wrapped(self._min_value)
        return wrapped


class with_pg_increment:
    def __init__(self, increment: int):
        self._increment = increment

    def __call__(self, wrapped) -> type:
        if not isinstance(wrapped, pg_sequence):
            raise TypeError('Decorated class must be a pg_sequence subclass')
        definition = getattr(wrapped, '__pg_definition')()
        assert 'increment' in definition
        assert definition['increment'] is None
        definition['increment'] = wrapped(self._increment)
        return wrapped
