from pgdriver.migration.backend.types.base import\
    mgr_module_id_seq,\
    mgr_module,\
    mgr_migration_operation_enum,\
    mgr_migration_id_seq,\
    mgr_migration,\
    mgr_object_id_seq,\
    mgr_object,\
    mgr_attribute_id_seq,\
    mgr_migration_change_type_enum,\
    mgr_attribute,\
    mgr_object_changelog,\
    mgr_diff_composite_definition
from pgdriver.migration.backend.types.composite import\
    mgr_composite,\
    mgr_composite_attribute
from pgdriver.migration.backend.types.domain import\
    mgr_domain
from pgdriver.migration.backend.types.enum import\
    mgr_enum,\
    mgr_enum_value
from pgdriver.migration.backend.types.sequence import\
    mgr_sequence
from pgdriver.migration.backend.types.table import\
    mgr_table,\
    mgr_table_column,\
    mgr_table_foreign_key_action,\
    mgr_table_foreign_key,\
    mgr_table_index_type,\
    mgr_table_index,\
    mgr_table_primary_key
from pgdriver.definition.base import\
    pg_composite


class mgr_composite_definition(pg_composite):
    composite: mgr_composite
    attributes: list[mgr_composite_attribute]


class mgr_table_definition(pg_composite):
    table: mgr_table
    columns: list[mgr_table_column]
    foreign_keys: list[mgr_table_foreign_key]
    indexes: list[mgr_table_index]
    primary_keys: list[mgr_table_primary_key]


class mgr_enum_definition(pg_composite):
    enum: mgr_enum
    values: list[mgr_enum_value]


class mgr_domain_definition(pg_composite):
    domain: mgr_domain


class mgr_sequence_definition(pg_composite):
    sequence: mgr_sequence
