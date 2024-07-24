from pydantic.dataclasses import\
    dataclass
from typing import\
    TypeAlias,\
    Literal,\
    Any,\
    Type,\
    Generic,\
    get_args
from pydantic_core import\
    core_schema
from pydantic import\
    GetCoreSchemaHandler,\
    ValidationInfo
from pgdriver.definition.tools.check import\
    Specification,\
    T


PGIndexType: TypeAlias = Literal['btree', 'hash', 'gin', 'brin', 'gist', 'spgist']


PGFKUpdateAction: TypeAlias = Literal['SET NULL', 'SET DEFAULT', 'RESTRICT', 'NO ACTION', 'CASCADE']


PGFKDeleteAction: TypeAlias = Literal['SET NULL', 'SET DEFAULT', 'RESTRICT', 'NO ACTION', 'CASCADE']


@dataclass(kw_only=True)
class pg_index_meta:
    name: str
    type: PGIndexType = 'btree'


@dataclass(kw_only=True)
class pg_unique_index_meta:
    name: str


@dataclass(kw_only=True)
class pg_primary_key_meta:
    name: str


@dataclass(kw_only=True)
class pg_foreign_key_meta:
    name: str
    other_class: type[Any]
    other_class_column_name: str
    on_update: PGFKUpdateAction = 'NO ACTION'
    on_delete: PGFKDeleteAction = 'NO ACTION'


# usar para describir el campo del modelo
@dataclass
class pg_comment_meta:
    value: str


@dataclass(kw_only=True)
class pg_check_meta(Generic[T]):
    predicate: Specification[T]
    name: str

    def __get_pydantic_core_schema__(
        self,
        source: Type[T],
        handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        if self.predicate is None:
            raise ValueError('Check predicate cannot be empty')
        schema = handler(source)
        # ignore class pg_check_meta[T] has no attribute __orig_class__ error
        # raised by mypy
        self.predicate.check_type(source, get_args(self.__orig_class__)[0])
        return core_schema.with_info_after_validator_function(
            function=self.validate,
            schema=schema,
            field_name=handler.field_name
        )

    def validate(self, value: T, info: ValidationInfo) -> T:
        self.predicate.check_value(value, info.data)
        return value

