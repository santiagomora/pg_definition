from pgdriver.definition.tools.decorators import\
    with_schema
from pgdriver.definition.tools.inspection import\
    extract_by_instance_type_from_inherited_classes
from pydantic_core import\
    core_schema
from pydantic import\
    Json
from decimal import\
    Decimal
from datetime import\
    datetime,\
    time,\
    date
from pgdriver.definition.tools import\
    pg_builtin


def _is_builtin(cls: type):
    bases: tuple[type] = extract_by_instance_type_from_inherited_classes(cls)
    return pg_builtin(cls.__name__, bases, dict(cls.__dict__))


@_is_builtin
@with_schema(core_schema.int_schema(strict=True, le=0x7fffffff))
class pg_int(int):
    pass


@_is_builtin
@with_schema(core_schema.int_schema(strict=True))
class pg_bigint(int):
    pass


@_is_builtin
@with_schema(core_schema.json_schema())
class pg_json(Json):
    pass


@_is_builtin
@with_schema(core_schema.str_schema(strict=True))
class pg_text(str):
    pass


@_is_builtin
@with_schema(core_schema.float_schema(strict=True))
class pg_float(float):
    pass


@_is_builtin
@with_schema(core_schema.bytes_schema(strict=True))
class pg_bytes(bytes):
    pass


@_is_builtin
@with_schema(core_schema.datetime_schema(strict=True, tz_constraint='naive'))
class pg_timestamp(datetime):
    pass


@_is_builtin
@with_schema(core_schema.datetime_schema(strict=True, tz_constraint='naive', now_op="past"))
class pg_past_timestamp(datetime):
    pass


@_is_builtin
@with_schema(core_schema.datetime_schema(strict=True, tz_constraint='naive', now_op="future"))
class pg_future_timestamp(datetime):
    pass


@_is_builtin
@with_schema(core_schema.datetime_schema(strict=True, tz_constraint='aware'))
class pg_timestamptz(datetime):
    pass


@_is_builtin
@with_schema(core_schema.datetime_schema(strict=True, tz_constraint='aware', now_op="past"))
class pg_past_timetstampz(date):
    pass


@_is_builtin
@with_schema(core_schema.datetime_schema(strict=True, tz_constraint='aware', now_op="future"))
class pg_future_timestamptz(date):
    pass


@_is_builtin
@with_schema(core_schema.time_schema(strict=True, tz_constraint='naive'))
class pg_time(time):
    pass


@_is_builtin
@with_schema(core_schema.time_schema(strict=True, tz_constraint='aware'))
class pg_timetz(time):
    pass


@_is_builtin
@with_schema(core_schema.date_schema(strict=True))
class pg_date(date):
    pass


@_is_builtin
@with_schema(core_schema.date_schema(strict=True, now_op="past"))
class pg_past_date(date):
    pass


@_is_builtin
@with_schema(core_schema.date_schema(strict=True, now_op="future"))
class pg_future_date(date):
    pass


@_is_builtin
@with_schema(core_schema.bool_schema(strict=True))
class pg_bool():
    pass


@_is_builtin
@with_schema(core_schema.decimal_schema(strict=True))
class pg_decimal(Decimal):
    pass


__all__ = {
    'pg_int': pg_int,
    'pg_bigint': pg_bigint,
    'pg_json': pg_json,
    'pg_text': pg_text,
    'pg_float': pg_float,
    'pg_bytes': pg_bytes,
    'pg_timestamp': pg_timestamp,
    'pg_past_timestamp': pg_past_timestamp,
    'pg_future_timestamp': pg_future_timestamp,
    'pg_timestamptz': pg_timestamptz,
    'pg_past_timetstampz': pg_past_timetstampz,
    'pg_future_timestamptz': pg_future_timestamptz,
    'pg_time': pg_time,
    'pg_timetz': pg_timetz,
    'pg_date': pg_date,
    'pg_past_date': pg_past_date,
    'pg_future_date': pg_future_date,
    'pg_bool': pg_bool,
    'pg_decimal': pg_decimal}
