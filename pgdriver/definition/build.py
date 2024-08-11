from enum import\
    Enum
from typing import\
    Any,\
    Callable
from pydantic_core import\
    core_schema,\
    SchemaValidator
from pydantic import\
    BaseModel,\
    GetCoreSchemaHandler
from pydantic import\
    Json
from decimal import\
    Decimal
from datetime import\
    datetime,\
    time,\
    date
from pgdriver.definition.inspection import\
    extract_by_instance_type_from_inherited_classes


class pg_builtin(type):
    pass


class pg_domain(pg_builtin):
    pass


class pg_sequence(pg_builtin):
    pass


class pg_enum(metaclass=Enum):
    pass


class pg_composite(BaseModel):
    pass


class pg_table(BaseModel):
    pass


def _with_schema(schema: core_schema.CoreSchema) -> Callable[type, type]:
    def inject_schema(wrapped_cls: type) -> type:
        bases: tuple[type] = extract_by_instance_type_from_inherited_classes(wrapped_cls)

        def __new__(cls, *args, **kwargs):
            validator: SchemaValidator = SchemaValidator(schema)
            validator.validate_python(*args)
            return bases[0].__new__(bases[0], *args, **kwargs)

        @classmethod
        def __get_pydantic_core_schema__(cls, source: type[Any], handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
            return schema

        return type(wrapped_cls.__name__, bases, dict(wrapped_cls.__dict__) | {
            '__new__': __new__,
            '__get_pydantic_core_schema__': __get_pydantic_core_schema__})
    return inject_schema


@_with_schema(core_schema.int_schema(strict=True, le=0x7fffffff, ge=-0x7fffffff))
class pg_int(int, metaclass=pg_builtin):
    pass


@_with_schema(core_schema.int_schema(strict=True))
class pg_bigint(int, metaclass=pg_builtin):
    pass


@_with_schema(core_schema.int_schema(strict=True, le=0x7fff, ge=-0x7fff))
class pg_smallint(int, metaclass=pg_builtin):
    pass


@_with_schema(core_schema.json_schema())
class pg_json(Json, metaclass=pg_builtin):
    pass


@_with_schema(core_schema.str_schema(strict=True))
class pg_text(str, metaclass=pg_builtin):
    pass


@_with_schema(core_schema.float_schema(strict=True))
class pg_double(float, metaclass=pg_builtin):
    pass


@_with_schema(core_schema.bytes_schema(strict=True))
class pg_bytes(bytes, metaclass=pg_builtin):
    pass


@_with_schema(core_schema.datetime_schema(strict=True, tz_constraint='naive'))
class pg_timestamp(datetime, metaclass=pg_builtin):
    pass


@_with_schema(core_schema.datetime_schema(strict=True, tz_constraint='naive', now_op="past"))
class pg_past_timestamp(datetime, metaclass=pg_builtin):
    pass


@_with_schema(core_schema.datetime_schema(strict=True, tz_constraint='naive', now_op="future"))
class pg_future_timestamp(datetime, metaclass=pg_builtin):
    pass


@_with_schema(core_schema.datetime_schema(strict=True, tz_constraint='aware'))
class pg_timestamptz(datetime, metaclass=pg_builtin):
    pass


@_with_schema(core_schema.datetime_schema(strict=True, tz_constraint='aware', now_op="past"))
class pg_past_timetstampz(datetime, metaclass=pg_builtin):
    pass


@_with_schema(core_schema.datetime_schema(strict=True, tz_constraint='aware', now_op="future"))
class pg_future_timestamptz(datetime, metaclass=pg_builtin):
    pass


@_with_schema(core_schema.time_schema(strict=True, tz_constraint='naive'))
class pg_time(time, metaclass=pg_builtin):
    pass


@_with_schema(core_schema.time_schema(strict=True, tz_constraint='aware'))
class pg_timetz(time, metaclass=pg_builtin):
    pass


@_with_schema(core_schema.date_schema(strict=True))
class pg_date(date, metaclass=pg_builtin):
    pass


@_with_schema(core_schema.date_schema(strict=True, now_op="past"))
class pg_past_date(date, metaclass=pg_builtin):
    pass


@_with_schema(core_schema.date_schema(strict=True, now_op="future"))
class pg_future_date(date, metaclass=pg_builtin):
    pass


@_with_schema(core_schema.bool_schema(strict=True))
class pg_bool(metaclass=pg_builtin):
    pass


@_with_schema(core_schema.decimal_schema(strict=True))
class pg_decimal(Decimal, metaclass=pg_builtin):
    pass
