from .predicate import\
    this,\
    field,\
    literal,\
    length,\
    LogicOperand,\
    OperandDefinitionContext
from pydantic_core import\
    core_schema
from pydantic import\
    GetCoreSchemaHandler,\
    ValidationInfo
from typing import\
    Any,\
    TypeVar,\
    Optional
from dataclasses import\
    dataclass
from ..sequence import\
    sequence
from ..common.inspection import\
    is_optional


class _TypeCompatibility(dict[type, type]):
    def register(self, for_type: type, compatible_with: type) -> None:
        if for_type in self:
            raise Exception(f'Cant overwrite {for_type} compatibility.')
        self[for_type] = compatible_with

    def get_supertype(self, for_type: type) -> Optional[type]:
        for t in self:
            if issubclass(for_type, t):
                return t
        return None


T = TypeVar('T')


class meta:
    class check:
        type_compatibility: _TypeCompatibility = _TypeCompatibility()

        def __init__(self, name: str, predicate: LogicOperand) -> None:
            self.predicate = predicate
            self.name = name
            self._source = None

        def __repr__(self):
            return f'meta.check(name={self.name}, predicate={repr(self.predicate)})'

        def __str__(self):
            return f'({str(self.predicate)})'

        def _validate(self, value: Any, info_data: Optional[ValidationInfo] = None) -> Any:
            if not self.predicate.value(value, {} if info_data is None else info_data):
                raise ValueError(f'{self.name}: constraint validation failed for value "{value}"')
            return value

        def __get_pydantic_core_schema__(self, source: type,
                                        handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
            self._source = source
            return core_schema.with_info_after_validator_function(
                function=self.validate_value,
                schema=handler(source),
                field_name=handler.field_name)

        def validate_value(self, value: Any, info: ValidationInfo) -> Any:
            if value is None:
                definition = getattr(self._source, '__pg_definition')()
                value = definition['default_value'] if 'default_value' in definition else value
            return self._validate(value, info.data)

    @dataclass
    class comment:
        value: str

    class default_value:
        def __repr__(self) -> str:
            return f'meta.default_value({self.default})'

        def __str__(self) -> str:
            return f'{self.default}'

        def __init__(self, *args, **kwargs) -> None:
            self.default = literal(*args, **kwargs)

        def __get_pydantic_core_schema__(self, source: type,
                                        handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
            # self._source = source
            # base: type = get_args(self.__orig_bases__)[0]
            # errors: list[str] = []
            # if not is_optional(source):
            #     errors.append('Annotated type must be optional')
            # if base not in get_args(source):
            #     errors.append('Base type must match annotated type')
            # if len(errors) > 0:
            #     raise TypeError(', '.join(errors))
            # # ignore class table_meta.meta.check[T] has no attribute __orig_class__ error
            # # raised by mypy
            return core_schema.with_info_after_validator_function(
                function=self.validate_value,
                schema=handler(source),
                field_name=handler.field_name)

        def validate_value(self, value: Any, info: ValidationInfo) -> Any:
            if value is None:
                return self.default.value(value, info)
            return value

    @dataclass
    class default_nextval:
        seq: sequence

        def __get_pydantic_core_schema__(self, source: type, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
            base_seq: type = getattr(self.seq, '__pg_definition')()['base_type']
            errors: list[str] = []
            if is_optional(source):
                errors.append('Annotated type must not be optional')
            if base_seq is not source:
                errors.append('Sequence type must match annotated type')
            if len(errors) > 0:
                raise TypeError(', '.join(errors))
            # ignore class table_meta.meta.check[T] has no attribute __orig_class__ error
            # raised by mypy
            return core_schema.with_info_after_validator_function(
                function=self.validate,
                schema=handler(source),
                field_name=handler.field_name)

        def validate(self, value: Any, info: ValidationInfo) -> Any:
            # if value is None:
            #    raise ValueError(f'Sequence {self.seq.__name__} value cant be empty')
            definition = getattr(self.seq, '__pg_definition')()
            if definition['min_value'] is not None and definition['min_value'] > value:
                raise ValueError('Value cant be less than sequence min value')
            if definition['max_value'] is not None and definition['max_value'] < value:
                raise ValueError('Value cant be greater than sequence max value')
            return value
