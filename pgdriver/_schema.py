from .definition.schema import\
    schema
import pgdriver.definition.builtin as build


class pg_catalog(schema):
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


