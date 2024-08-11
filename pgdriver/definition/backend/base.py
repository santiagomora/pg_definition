from pgdriver.definition.build import\
    pg_composite,\
    pg_text,\
    pg_int,\
    pg_bool,\
    pg_bigint,\
    pg_enum
from typing import\
    Optional
from pgdriver.definition.registry import\
    valid_pg_definition


@valid_pg_definition
class def_table_index_type(pg_enum):
    BTREE = 'btree'
    HASH = 'hash'
    GIN = 'gin'
    BRIN = 'brin'
    GIST = 'gist'
    SPGIST = 'spgist'


@valid_pg_definition
class def_table_foreign_key_action(pg_enum):
    SET_NULL = 'SET NULL'
    SET_DEFAULT = 'SET DEFAULT'
    RESTRICT = 'RESTRICT'
    NO_ACTION = 'NO ACTION'
    CASCADE = 'CASCADE'


@valid_pg_definition
class def_attribute_definition(pg_composite):
    name: pg_text
    order: pg_int
    check_constraint: pg_text
    comment: pg_text
    type_name: pg_text


@valid_pg_definition
class def_composite_definition(pg_composite):
    name: pg_text
    schema_name: pg_text
    attributes: list[def_attribute_definition]
    comment: Optional[pg_text]


@valid_pg_definition
class def_column_definition(pg_composite):
    name: pg_text
    order: pg_int
    check_constraint: pg_text
    comment: pg_text
    type_name: pg_text


@valid_pg_definition
class def_foreign_key_definition(pg_composite):
    name: pg_text
    class_column_name: tuple[pg_text]
    other_class_name: pg_text
    other_class_column_name: tuple[pg_text]
    on_delete: def_table_foreign_key_action
    on_update: def_table_foreign_key_action


@valid_pg_definition
class def_primary_key_definition(pg_composite):
    name: pg_text
    column_name: tuple[pg_text]


@valid_pg_definition
class def_index_definition(pg_composite):
    name: pg_text
    column_name: tuple[pg_text]
    type: def_table_index_type
    is_unique: pg_bool


@valid_pg_definition
class def_table_definition(pg_composite):
    name: pg_text
    schema_name: pg_text
    base_classes: tuple[pg_text]
    comment: Optional[pg_text]
    columns: list[def_column_definition]
    foreign_keys: list[def_foreign_key_definition]
    indexes: list[def_index_definition]
    primary_key: Optional[def_primary_key_definition]


@valid_pg_definition
class def_enum_value_definition(pg_composite):
    value: pg_text
    order: pg_int


@valid_pg_definition
class def_enum_definition(pg_composite):
    name: pg_text
    schema_name: pg_text
    comment: Optional[pg_text]
    values: list[def_enum_value_definition]


@valid_pg_definition
class def_domain_definition(pg_composite):
    name: pg_text
    schema_name: pg_text
    comment: Optional[pg_text]
    type_name: pg_text


@valid_pg_definition
class def_sequence_definition(pg_composite):
    name: pg_text
    schema_name: pg_text
    comment: Optional[pg_text]
    type_name: pg_text
    max_value: pg_bigint
    min_value: pg_bigint
