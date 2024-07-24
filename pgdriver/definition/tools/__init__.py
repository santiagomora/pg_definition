from pgdriver.adapt.pydantic import\
    PGBaseModel
from abc import\
    ABC
from enum import\
    EnumType
from pydantic.dataclasses import\
    dataclass
from pgdriver.definition.tools.metadata import\
    PGFKUpdateAction,\
    PGFKDeleteAction,\
    PGIndexType


class pg_builtin(type):
    pass


class pg_composite(PGBaseModel, ABC):
    pass


class pg_domain(pg_builtin):
    pass


class pg_table(PGBaseModel, ABC):
    pass


class pg_enum(EnumType):
    pass


@dataclass(kw_only=True)
class pg_foreign_key:
    fk_name: str
    fk_other_class: type[pg_table]
    fk_other_class_column_names: tuple[str]
    fk_class_column_names: tuple[str]
    fk_on_update: PGFKUpdateAction
    fk_on_delete: PGFKDeleteAction


@dataclass(kw_only=True)
class pg_index:
    ix_name: str
    ix_type: PGIndexType


@dataclass(kw_only=True)
class pg_unique_index:
    uix_name: str
    uix_column_names: tuple[str]


@dataclass(kw_only=True)
class pg_primary_key:
    pk_name: str
    pk_column_names: tuple[str]
