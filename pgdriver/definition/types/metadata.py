from dataclasses import\
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
from .check import\
    Specification,\
    T


PGIndexType: TypeAlias = Literal['btree', 'hash', 'gin', 'brin', 'gist', 'spgist']


PGFKUpdateAction: TypeAlias = Literal['SET NULL', 'SET DEFAULT', 'RESTRICT', 'NO ACTION', 'CASCADE']


PGFKDeleteAction: TypeAlias = Literal['SET NULL', 'SET DEFAULT', 'RESTRICT', 'NO ACTION', 'CASCADE']


@dataclass(kw_only=True)
class pg_index:
    name: str
    type: PGIndexType = 'btree'


@dataclass(kw_only=True)
class pg_unique:
    name: str


@dataclass(kw_only=True)
class pg_primary_key:
    name: str


# TODO aqui hay que hacer una validacion en el modelo other_class porque el
# campo al que apunta la fk deben ser indice y debe ser del mismo tipo
# TODO hacer una manera de sacar __name__ sin acceder directamente a __name__
# * los campos a los que apuntan la foreign key deben ser del mismo tipo que la 
# en la tabla que los define
# * los campos a los que apuntan la foreign key deben ser del mismo tipo que la 
# que los define
# * los set de nombre de campo local y foraneo deben tener el mismo tamano
# * los campos de on_update y on_delete debe coincidir en todos los elementos
# de la llave de un mismo nombre
# * la tabla en las llaves de un mismo nombre deben coincidir
# * la precondicion es que las foreign_key compartan el mismo nombre
@dataclass(kw_only=True)
class pg_foreign_key:
    name: str
    other_class: type[Any]
    other_class_column_name: str
    on_update: PGFKUpdateAction = 'NO ACTION'
    on_delete: PGFKDeleteAction = 'NO ACTION'


# usar para describir el campo del modelo
@dataclass
class pg_comment:
    value: str


@dataclass(kw_only=True)
class pg_check(Generic[T]):
    # no es tan sencillo, hay que modelarlo como un predicado que puede tener
    # conjuncion con varias columnas de la tabla, pero tambien debe ser usable 
    # cuando hablamos de domains, tanto composite como tipos simples
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
        # ignore class pg_check[T] has no attribute __orig_class__ error
        # raised by mypy
        self.predicate.check_type(source, get_args(self.__orig_class__)[0]) # type: ignore[attr-defined]
        return core_schema.with_info_after_validator_function(
            function=self.validate,
            schema=schema,
            field_name=handler.field_name
        )

    def validate(self, value: T, info: ValidationInfo) -> T:
        self.predicate.check_value(value, info)
        return value
