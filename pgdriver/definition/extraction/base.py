from typing import\
    Optional
from enum import\
    Enum
from pydantic import\
    BaseModel


class pg_table_index_type(Enum):
    BTREE = 'btree'
    HASH = 'hash'
    GIN = 'gin'
    BRIN = 'brin'
    GIST = 'gist'
    SPGIST = 'spgist'


class pg_table_foreign_key_action(Enum):
    SET_NULL = 'SET NULL'
    SET_DEFAULT = 'SET DEFAULT'
    RESTRICT = 'RESTRICT'
    NO_ACTION = 'NO ACTION'
    CASCADE = 'CASCADE'


class pg_attribute_definition(BaseModel):
    name: str
    order: int
    check_constraint: str
    comment: str
    type_name: str


class pg_composite_definition(BaseModel):
    name: str
    schema_name: str
    attributes: list[pg_attribute_definition]
    comment: Optional[str]


class pg_column_definition(BaseModel):
    name: str
    order: int
    check_constraint: str
    comment: str
    type_name: str


class pg_foreign_key_definition(BaseModel):
    name: str
    class_column_name: tuple[str]
    other_class_name: str
    other_class_column_name: tuple[str]
    on_delete: pg_table_foreign_key_action
    on_update: pg_table_foreign_key_action


class pg_primary_key_definition(BaseModel):
    name: str
    column_name: tuple[str]


class pg_index_definition(BaseModel):
    name: str
    column_name: tuple[str]
    type: pg_table_index_type
    is_unique: bool


class pg_table_definition(BaseModel):
    name: str
    schema_name: str
    base_classes: tuple[str]
    comment: Optional[str]
    columns: list[pg_column_definition]
    foreign_keys: list[pg_foreign_key_definition]
    indexes: list[pg_index_definition]
    primary_key: Optional[pg_primary_key_definition]


class pg_enum_value_definition(BaseModel):
    value: str
    order: int


class pg_enum_definition(BaseModel):
    name: str
    schema_name: str
    comment: Optional[str]
    values: list[pg_enum_value_definition]


class pg_domain_definition(BaseModel):
    name: str
    schema_name: str
    comment: Optional[str]
    check_constraint: Optional[str]
    base_type_name: str


class pg_sequence_definition(BaseModel):
    name: str
    schema_name: str
    comment: Optional[str]
    base_type_name: str
    max_value: int
    min_value: int
