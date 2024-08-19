from pgdriver.definition.flows import\
    FlowAccumulator,\
    FlowComponentException,\
    DefinitionFlow,\
    FlowComponent
from pgdriver.definition.build import\
    pg_domain,\
    pg_composite
from typing import\
    Any,\
    Callable
from pydantic_core import\
    core_schema,\
    SchemaValidator
from pydantic import\
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


pg_domain_definition_flow: DefinitionFlow = DefinitionFlow('pgdriver-domain-definition-flow')


class pg_builtin(type):
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        accumulator: FlowAccumulator = FlowAccumulator()
        pg_domain_definition_flow.execute(cls, accumulator)


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


class DomainValidateTargetMetaclassComponent(FlowComponent[pg_domain]):
    """
    target type must be an instance of pg_domain and pg_builtin
    """

    def __init__(self):
        super().__init__('validate-target-metaclass-component')

    def execute(self, target: type[pg_domain], accumulator: FlowAccumulator) -> None:
        errors: list[str] = []
        if not isinstance(target, pg_domain):
            errors.append(f'Target type {type} must be a pg_domain instance')
        if not isinstance(target, pg_builtin):
            errors.append(f'Target type {type} must be a pg_builtin instance')
        if not isinstance(target, pg_composite):
            errors.append(f'Target type {type} must be a pg_composite instance')
        if len(errors) > 0:
            raise FlowComponentException(self.name, [' or '.join(errors)])


class DomainStoreFinalDefinitionComponent(FlowComponent[pg_domain]):
    """
    Stores final definition
    """

    def __init__(self):
        super().__init__('domain-store-final-definition-component')

    def execute(self, target: type[pg_domain], accumulator: FlowAccumulator) -> None:
        accumulator.add_definition('final', {})

    def get_dependencies(self) -> tuple[str]:
        return ('validate-target-metaclass-component', )


with pg_domain_definition_flow.at_work_path('validation') as flow:
    flow.register(DomainValidateTargetMetaclassComponent())

with pg_domain_definition_flow.at_work_path('') as flow:
    flow.register(DomainStoreFinalDefinitionComponent())

__all__ = {
    'pg_int': pg_int,
    'pg_bigint': pg_bigint,
    'pg_smallint': pg_smallint,
    'pg_json': pg_json,
    'pg_text': pg_text,
    'pg_double': pg_double,
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
