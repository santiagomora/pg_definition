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
from .definition.function import\
    single_result_function,\
    set_returning_function,\
    discard_result_function,\
    register_overload
from datetime import\
    datetime,\
    time,\
    date as _date
from typing_extensions import\
    Annotated
from enum import\
    auto
from .definition.permission import\
    permission,\
    grant
from .definition.schema import\
    schema,\
    register_function_path_alias
from ._schema import\
    pg_catalog,\
    register_types
from .definition.builtin import\
    builtin
from ._adapter_registry import\
    adapter_registry,\
    AdapterRegistry


__all__ = ['pg_catalog', 'builtin', 'register_types', 'register_function_path_alias', 'permission', 'grant', 'register_overload', 'schema', 'composite', 'table', 'meta', 'index_type', 'foreign_key_action', 'index', 'unique_constraint', 'primary_key', 'foreign_key', 'enums', 'LogicOperand', 'OperandDefinitionContext', 'this', 'field', 'literal', 'length', 'int8_sequence', 'int4_sequence', 'int2_sequence', 'sequence', 'builtin', 'int4', 'int8', 'int2', 'float4', 'text', 'char', 'float8', 'bytea', 'timestamptz', 'timetz', 'date', 'bool', 'single_result_function', 'set_returning_function', 'discard_result_function', 'NodeException', 'FlowException', 'adapter_registry', 'AdapterRegistry', 'Annotated', 'auto', 'in_schema', 'increment', 'max_value', 'min_value']


meta.check.type_compatibility.register(pg_catalog.int8, Number)
meta.check.type_compatibility.register(pg_catalog.int4, Number)
meta.check.type_compatibility.register(pg_catalog.int2, Number)
meta.check.type_compatibility.register(pg_catalog.float8, Number)
meta.check.type_compatibility.register(pg_catalog.float4, Number)
meta.check.type_compatibility.register(pg_catalog.timetz, time)
meta.check.type_compatibility.register(pg_catalog.date, _date)
meta.check.type_compatibility.register(pg_catalog.text, str)
meta.check.type_compatibility.register(pg_catalog.timestamptz, datetime)
meta.check.type_compatibility.register(pg_catalog.bool, bool)
meta.check.type_compatibility.register(composite, composite)
meta.check.type_compatibility.register(table, composite)


int4 = pg_catalog.int4
int8 = pg_catalog.int8
int2 = pg_catalog.int2
float4 = pg_catalog.float4
text = pg_catalog.text
char = pg_catalog.char
float8 = pg_catalog.float8
bytea = pg_catalog.bytea
timestamptz = pg_catalog.timestamptz
timetz = pg_catalog.timetz
date = pg_catalog.date
bool = pg_catalog.bool


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
