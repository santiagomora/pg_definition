from .types.schema import\
    schema
import pg_definition.types.builtin as build
from ._adapter_registry import\
    AdapterRegistry


class pg_catalog(schema):
    int4: type[build.int4] = build.int4
    int8: type[build.int8] = build.int8
    int2: type[build.int2] = build.int2
    float4: type[build.float4] = build.float4
    text: type[build.text] = build.text
    char: type[build.char] = build.char
    float8: type[build.float8] = build.float8
    bytea: type[build.bytea] = build.bytea
    timestamptz: type[build.timestamptz] = build.timestamptz
    timetz: type[build.timetz] = build.timetz
    date: type[build.date] = build.date
    bool: type[build.bool] = build.bool


def register_types(ar: AdapterRegistry):
    ar.register_type(pg_catalog.int4)
    ar.register_type(pg_catalog.int8)
    ar.register_type(pg_catalog.int2)
    ar.register_type(pg_catalog.float4)
    ar.register_type(pg_catalog.text)
    ar.register_type(pg_catalog.char, '"char"')
    ar.register_type(pg_catalog.float8)
    ar.register_type(pg_catalog.bytea)
    ar.register_type(pg_catalog.timestamptz)
    ar.register_type(pg_catalog.timetz)
    ar.register_type(pg_catalog.date)
    ar.register_type(pg_catalog.bool)
