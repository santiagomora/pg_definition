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
    Type,\
    TypeVar,\
    Optional
from dataclasses import\
    dataclass
from enum import\
    Enum
from ..sequence import\
    sequence
from ..common.model import\
    table
from ..common.inspection import\
    is_optional,\
    extract_type


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


class check:
    type_compatibility: _TypeCompatibility = _TypeCompatibility()

    def __init__(self, *, name: str, predicate: LogicOperand) -> None:
        self.predicate = predicate
        self.name = name
        self._source = None

    def __repr__(self):
        return f'check(name={self.name}, predicate={repr(self.predicate)})'

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


T = TypeVar('T')


class default_value:
    def __repr__(self) -> str:
        return f'default_value({self.default})'

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
        # # ignore class table_meta.check[T] has no attribute __orig_class__ error
        # # raised by mypy
        return core_schema.with_info_after_validator_function(
            function=self.validate_value,
            schema=handler(source),
            field_name=handler.field_name)

    def validate_value(self, value: Any, info: ValidationInfo) -> Any:
        if value is None:
            return self.default.value(value, info)
        return value


class index_type(Enum):
    BTREE = 'btree'
    HASH = 'hash'
    GIN = 'gin'
    BRIN = 'brin'
    GIST = 'gist'
    SPGIST = 'spgist'


class foreign_key_action(Enum):
    SET_NULL = 'SET NULL'
    SET_DEFAULT = 'SET DEFAULT'
    RESTRICT = 'RESTRICT'
    NO_ACTION = 'NO ACTION'
    CASCADE = 'CASCADE'


T = TypeVar("T")


@dataclass(kw_only=True)
class index:
    name: str
    type: index_type = index_type.BTREE


@dataclass(kw_only=True)
class unique_index:
    name: str
    type: index_type = index_type.BTREE


@dataclass(kw_only=True)
class primary_key:
    name: str


@dataclass(kw_only=True)
class foreign_key:
    name: str
    other_class: type[table]
    other_class_column_name: str
    on_update: foreign_key_action = foreign_key_action.NO_ACTION
    on_delete: foreign_key_action = foreign_key_action.NO_ACTION

    def __get_pydantic_core_schema__(self, source: Type[T], handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        if not issubclass(self.other_class, table):
            raise TypeError(f'Other class {self.other_class} must be a {table} instance')
        if self.other_class_column_name not in self.other_class.model_fields:
            raise TypeError(f'Foreign key column {self.other_class_column_name} must exist in {self.other_class} definition')
        other_class_column: FieldInfo = self.other_class.model_fields[self.other_class_column_name]
        if extract_type(other_class_column.annotation) != extract_type(source):
            raise TypeError(f'Foreign key column {handler.field_name} type must match with {self.other_class_column_name} in {self.other_class} definition')
        schema: core_schema.CoreSchema = handler(source)
        # ignore class check[T] has no attribute __orig_class__ error
        # raised by mypy
        return schema


@dataclass(kw_only=True)
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
        # ignore class table_meta.check[T] has no attribute __orig_class__ error
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
