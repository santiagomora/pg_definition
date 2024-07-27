from pgdriver.adapt.pydantic import\
    PGBaseModel
from abc import\
    ABC
from typing import\
    Optional
from enum import\
    EnumType
from pydantic.dataclasses import\
    dataclass
from pgdriver.definition.metadata import\
    PGFKUpdateAction,\
    PGFKDeleteAction,\
    PGIndexType
from pgdriver.definition.metadata import\
    pg_comment_meta,\
    pg_check_meta


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


@dataclass(kw_only=True)
class pg_column:
    col_name: str
    col_type: str
    col_check: Optional[pg_check_meta]
    col_comment: Optional[pg_comment_meta]


@dataclass(kw_only=True)
class pg_attribute:
    attr_name: str
    attr_type: str
    attr_check: Optional[pg_check_meta]


@dataclass(kw_only=True)
class pg_check:
    ck_field_name: str
    ck_meta: pg_check_meta
