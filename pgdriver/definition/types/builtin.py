from pgdriver.adapt.pydantic import\
    _AwareTime,\
    _NaiveTime
from .representable import\
    PGRepresentable
from pydantic.dataclasses import\
    dataclass
from typing import\
    Annotated
from abc import\
    abstractmethod,\
    abstractclassmethod
from typing import\
    Any
from annotated_types import\
    Le
from pydantic import\
    AwareDatetime,\
    NaiveDatetime,\
    Strict,\
    Json
from decimal import\
    Decimal
from pydantic_core import\
    core_schema,\
    SchemaValidator
from pydantic.annotated_handlers import\
    GetCoreSchemaHandler
from datetime import\
    datetime,\
    time,\
    date


class PGBuiltinDefinition:
    identifier: str


# class pg_builtin(PGRepresentable[PGBuiltinDefinition], ABC):
#     pass


class pg_builtin(type):
    def __new__(cls, clsname, bases, clsdict):
        schema: core_schema.CoreSchema = clsdict[f'_{clsname}__schema']

        def __new__(cls, *args, **kwargs):
            validator: SchemaValidator = SchemaValidator(schema)
            validator.validate_python(*args)
            return bases[0].__new__(bases[0], *args)

        @classmethod
        def __get_pydantic_core_schema__(cls, source: type[Any], handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
            return schema

        clsdict |= {
            '__new__': __new__,
            '__get_pydantic_core_schema__': __get_pydantic_core_schema__}
        return super().__new__(cls, clsname, bases, clsdict)


class pg_int(int, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.int_schema(strict=True, le=0x7fffffff)


class pg_schema(str, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.str_schema(strict=True)


class pg_bigint(int, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.int_schema(strict=True)


class pg_json(Json, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.json_schema()


class pg_text(str, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.str_schema(strict=True)


class pg_float(float, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.float_schema(strict=True)


class pg_bytes(bytes, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.bytes_schema(strict=True)


class pg_timestamp(datetime, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.datetime_schema(strict=True, tz_constraint='naive')


class pg_past_timestamp(datetime, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.datetime_schema(strict=True, tz_constraint='naive', now_op="past")


class pg_future_timestamp(datetime, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.datetime_schema(strict=True, tz_constraint='naive', now_op="future")


class pg_timestamptz(datetime, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.datetime_schema(strict=True, tz_constraint='aware')


class pg_past_timetstampz(date, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.datetime_schema(strict=True, tz_constraint='aware', now_op="past")


class pg_future_timestamptz(date, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.datetime_schema(strict=True, tz_constraint='aware', now_op="future")


class pg_time(time, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.time_schema(strict=True, tz_constraint='naive')


class pg_timetz(time, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.time_schema(strict=True, tz_constraint='aware')


class pg_date(date, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.date_schema(strict=True)


class pg_past_date(date, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.date_schema(strict=True, now_op="past")


class pg_future_date(date, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.date_schema(strict=True, now_op="future")


class pg_bool(metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.bool_schema(strict=True)


class pg_decimal(Decimal, metaclass=pg_builtin):
    __schema: core_schema.CoreSchema = core_schema.decimal_schema(strict=True)
    # def __new__(cls, *args, **kwargs):
    #     max_digits, decimal_places = cls.get_decimal_description()
    #     validator: SchemaValidator = SchemaValidator(core_schema.decimal_schema(strict=True, max_digits=max_digits, decimal_places=decimal_places))
    #     validator.validate_python(*args)
    #     return super(pg_decimal, cls).__new__(cls, *args)
    # 
    # @classmethod
    # def __get_pydantic_core_schema__(cls, source: type[Any], handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
    #     max_digits, decimal_places = cls.get_decimal_description()
    # 
    # @abstractclassmethod
    # def get_decimal_description(cls) -> tuple[int, int]:
    #     pass
