from numbers import\
    Number
from .definition.composite import\
    composite
from .definition.table import\
    table
from .definition.common.flow import\
    NodeException,\
    FlowException
from .definition.enums import\
    enums
from .definition.meta.predicate import\
    LogicOperand,\
    OperandDefinitionContext,\
    this,\
    field,\
    literal,\
    length
from .definition.meta import\
    check,\
    comment,\
    default_value,\
    index_type,\
    foreign_key_action,\
    index,\
    unique_index,\
    primary_key,\
    foreign_key,\
    default_nextval
from .definition.sequence import\
    bigint_sequence,\
    integer_sequence,\
    smallint_sequence,\
    sequence
from .definition.builtin import\
    builtin,\
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
    boolean
from .definition.function import\
    single_result_function,\
    set_returning_function,\
    perform_function
from datetime import\
    datetime,\
    time,\
    date as _date
from .adapter_registry import\
    adapter_registry
from .extension import\
    Extension


__all__ = ['composite', 'table', 'index_type', 'foreign_key_action', 'index', 'unique_index', 'primary_key', 'foreign_key', 'default_nextval', 'enums', 'LogicOperand', 'OperandDefinitionContext', 'this', 'field', 'literal', 'length', 'check', 'comment', 'default_value', 'bigint_sequence', 'integer_sequence', 'smallint_sequence', 'sequence', 'builtin', 'integer', 'bigint', 'smallint', 'real', 'text', 'char', 'double', 'byte', 'timestamptz', 'timetz', 'date', 'boolean', 'single_result_function', 'set_returning_function', 'perform_function', 'NodeException', 'FlowException', 'adapter_registry', 'Extension']


check.type_compatibility.register(bigint, Number)
check.type_compatibility.register(integer, Number)
check.type_compatibility.register(smallint, Number)
check.type_compatibility.register(double, Number)
check.type_compatibility.register(real, Number)
check.type_compatibility.register(timetz, time)
check.type_compatibility.register(date, _date)
check.type_compatibility.register(text, str)
check.type_compatibility.register(timestamptz, datetime)
check.type_compatibility.register(boolean, bool)
check.type_compatibility.register(composite, composite)


def with_default_value(*args, **kwargs):

    def _add_to_definition(target: type):
        # esto va a cambiar, no se deberia poder acceder a la definicion directamente
        # __pg_definition deberia devolver una copia siempre
        # no puede usarse con table o composite
        assert hasattr(target.__bases__[0], '__pg_definition')
        definition = getattr(target, '__pg_definition')()
        assert definition['default_value'] is None
        value: default_value = default_value(*args, **kwargs)
        value.default.propagate_definition(target, None, OperandDefinitionContext.BUILTIN_DOMAIN)
        definition['default_value'] = value
        return target

    return _add_to_definition


def with_comment(value: str):

    def _add_to_definition(target: type):
        # esto va a cambiar, no se deberia poder acceder a la definicion directamente
        # esto deberia devolver una copia siempre
        definition = getattr(target, '__pg_definition')()
        assert definition['comment'] is None
        assert isinstance(value, str)
        definition['comment'] = comment(value)
        return target

    return _add_to_definition


class with_check:
    def __init__(self, name: str,  predicate: LogicOperand) -> None:
        self._check: check = check(name=name, predicate=predicate)

    def __call__(self, target: type):
        definition = getattr(target, '__pg_definition')()
        assert definition['check'] is None
        self._check.predicate.propagate_definition(target, None, OperandDefinitionContext.BUILTIN_DOMAIN)
        definition['check'] = self._check
        return target


class with_max_value:
    def __init__(self, max_value: int):
        self._max_value = max_value

    def __call__(self, wrapped) -> type:
        if not isinstance(wrapped, sequence):
            raise TypeError('Decorated class must be a sequence subclass')
        definition = getattr(wrapped, '__pg_definition')()
        assert 'max_value' in definition
        assert definition['max_value'] is None
        definition['max_value'] = wrapped(self._max_value)
        return wrapped


class with_min_value:
    def __init__(self, min_value: int):
        self._min_value = min_value

    def __call__(self, wrapped) -> type:
        if not isinstance(wrapped, sequence):
            raise TypeError('Decorated class must be a sequence subclass')
        definition = getattr(wrapped, '__pg_definition')()
        assert 'min_value' in definition
        assert definition['min_value'] is None
        definition['min_value'] = wrapped(self._min_value)
        return wrapped


class with_increment:
    def __init__(self, increment: int):
        self._increment = increment

    def __call__(self, wrapped) -> type:
        if not isinstance(wrapped, sequence):
            raise TypeError('Decorated class must be a sequence subclass')
        definition = getattr(wrapped, '__pg_definition')()
        assert 'increment' in definition
        assert definition['increment'] is None
        definition['increment'] = wrapped(self._increment)
        return wrapped
