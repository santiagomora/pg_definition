from numbers import\
    Number
from .definition.composite import\
    composite
from .definition.table import\
    table,\
    index_type,\
    foreign_key_action,\
    index,\
    unique_constraint,\
    primary_key,\
    foreign_key
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
    meta
from .definition.sequence import\
    int8_sequence,\
    int4_sequence,\
    int2_sequence,\
    sequence,\
    increment,\
    max_value,\
    min_value
import pgdriver.definition.builtin as build
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
from typing_extensions import\
    Annotated
from enum import\
    auto


__all__ = ['composite', 'table', 'meta', 'index_type', 'foreign_key_action', 'index', 'unique_constraint', 'primary_key', 'foreign_key', 'enums', 'LogicOperand', 'OperandDefinitionContext', 'this', 'field', 'literal', 'length', 'int8_sequence', 'int4_sequence', 'int2_sequence', 'sequence', 'builtin', 'int4', 'int8', 'int2', 'float4', 'text', 'char', 'float8', 'bytea', 'timestamptz', 'timetz', 'date', 'bool', 'single_result_function', 'set_returning_function', 'perform_function', 'NodeException', 'FlowException', 'adapter_registry', 'Extension', 'Annotated', 'auto', 'in_schema', 'increment', 'max_value', 'min_value']


meta.check.type_compatibility.register(build.int8, Number)
meta.check.type_compatibility.register(build.int4, Number)
meta.check.type_compatibility.register(build.int2, Number)
meta.check.type_compatibility.register(build.float8, Number)
meta.check.type_compatibility.register(build.float4, Number)
meta.check.type_compatibility.register(build.timetz, time)
meta.check.type_compatibility.register(build.date, _date)
meta.check.type_compatibility.register(build.text, str)
meta.check.type_compatibility.register(build.timestamptz, datetime)
meta.check.type_compatibility.register(build.bool, bool)
meta.check.type_compatibility.register(composite, composite)


builtin = build.builtin
int4 = build.int4
int8 = build.int8
int2 = build.int2
float4 = build.float4
text = build.text
char = build.char
float8 = build.float8
bytea = build.bytea
timestamptz = build.timestamptz
timetz = build.timetz
date = build.date
bool = build.bool


class check:
    def __init__(self, name: str,  predicate: LogicOperand) -> None:
        self.check_meta: meta.check = meta.check(name=name, predicate=predicate)

    def __call__(self, target: type):
        definition = getattr(target, '__pg_definition')()
        assert definition['check'] is None
        self.check_meta.predicate.propagate_definition(target, None, OperandDefinitionContext.BUILTIN_DOMAIN)
        definition['check'] = self.check_meta
        return target


def default_value(*args, **kwargs):

    def _add_to_definition(target: type):
        # esto va a cambiar, no se deberia poder acceder a la definicion directamente
        # __pg_definition deberia devolver una copia siempre
        # no puede usarse con table o composite
        assert hasattr(target.__bases__[0], '__pg_definition')
        definition = getattr(target, '__pg_definition')()
        assert definition['default_value'] is None
        value: meta.default_value = meta.default_value(*args, **kwargs)
        value.default.propagate_definition(target, None, OperandDefinitionContext.BUILTIN_DOMAIN)
        definition['default_value'] = value
        return target

    return _add_to_definition


def comment(value: str):

    def _add_to_definition(target: type):
        # esto va a cambiar, no se deberia poder acceder a la definicion directamente
        # esto deberia devolver una copia siempre
        definition = getattr(target, '__pg_definition')()
        assert definition['comment'] is None
        assert isinstance(value, str)
        definition['comment'] = meta.comment(value)
        return target

    return _add_to_definition


def in_schema(schema_name: str):

    def _add_to_definition(target: type):
        definition = getattr(target, '__pg_definition')()
        assert definition['schema'] is None
        assert isinstance(schema_name, str)
        definition['schema'] = schema_name
        return target

    return _add_to_definition
