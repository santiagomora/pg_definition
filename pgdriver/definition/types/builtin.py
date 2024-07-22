from pgdriver.definition.types.decorators import\
    with_schema
from pgdriver.definition.inspection import\
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


class pg_builtin(type):
    pass


def is_builtin(cls: type):
    bases: tuple[type] = extract_by_instance_type_from_inherited_classes(cls)
    return pg_builtin(cls.__name__, bases, dict(cls.__dict__))


@is_builtin
@with_schema(core_schema.int_schema(strict=True, le=0x7fffffff))
class pg_int(int):
    pass


@is_builtin
@with_schema(core_schema.str_schema(strict=True))
class pg_schema(str):
    pass


@is_builtin
@with_schema(core_schema.int_schema(strict=True))
class pg_bigint(int):
    pass


@is_builtin
@with_schema(core_schema.json_schema())
class pg_json(Json):
    pass


@is_builtin
@with_schema(core_schema.str_schema(strict=True))
class pg_text(str):
    pass


@is_builtin
@with_schema(core_schema.float_schema(strict=True))
class pg_float(float):
    pass


@is_builtin
@with_schema(core_schema.bytes_schema(strict=True))
class pg_bytes(bytes):
    pass


@is_builtin
@with_schema(core_schema.datetime_schema(strict=True, tz_constraint='naive'))
class pg_timestamp(datetime):
    pass


@is_builtin
@with_schema(core_schema.datetime_schema(strict=True, tz_constraint='naive', now_op="past"))
class pg_past_timestamp(datetime):
    pass


@is_builtin
@with_schema(core_schema.datetime_schema(strict=True, tz_constraint='naive', now_op="future"))
class pg_future_timestamp(datetime):
    pass


@is_builtin
@with_schema(core_schema.datetime_schema(strict=True, tz_constraint='aware'))
class pg_timestamptz(datetime):
    pass


@is_builtin
@with_schema(core_schema.datetime_schema(strict=True, tz_constraint='aware', now_op="past"))
class pg_past_timetstampz(date):
    pass


@is_builtin
@with_schema(core_schema.datetime_schema(strict=True, tz_constraint='aware', now_op="future"))
class pg_future_timestamptz(date):
    pass


@is_builtin
@with_schema(core_schema.time_schema(strict=True, tz_constraint='naive'))
class pg_time(time):
    pass


@is_builtin
@with_schema(core_schema.time_schema(strict=True, tz_constraint='aware'))
class pg_timetz(time):
    pass


@is_builtin
@with_schema(core_schema.date_schema(strict=True))
class pg_date(date):
    pass


@is_builtin
@with_schema(core_schema.date_schema(strict=True, now_op="past"))
class pg_past_date(date):
    pass


@is_builtin
@with_schema(core_schema.date_schema(strict=True, now_op="future"))
class pg_future_date(date):
    pass


@is_builtin
@with_schema(core_schema.bool_schema(strict=True))
class pg_bool():
    pass


@is_builtin
@with_schema(core_schema.decimal_schema(strict=True))
class pg_decimal(Decimal):
    pass
