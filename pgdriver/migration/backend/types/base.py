from pgdriver.definition.build import\
    pg_table,\
    pg_sequence,\
    pg_bigint,\
    pg_meta,\
    pg_datetime,\
    pg_enum,\
    pg_text,\
    pg_bool
from pgdriver.definition.registry import\
    valid_pg_definition
from typing_extensions import\
    Annotated
from typing import\
    Optional


@valid_pg_definition
class mgr_module_id_seq(pg_bigint, metaclass=pg_sequence):
    pass


@valid_pg_definition
class mgr_module(pg_table):
    id: Annotated[
        pg_bigint,
        pg_meta.default.nextval(mgr_module_id_seq),
        pg_meta.primary_key('mgr_module_id_pk')]
    name: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_module_name_uix')]
    schema_name: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_module_schema_name_uix')]


@valid_pg_definition
class mgr_migration_operation_enum(pg_enum):
    UP = 'up'
    DOWN = 'down'
    INSTALL = 'install'
    REMOVE = 'remove'


@valid_pg_definition
class mgr_migration_id_seq(pg_bigint, metaclass=pg_sequence):
    pass


@valid_pg_definition
class mgr_migration(pg_table):
    id: Annotated[
        pg_bigint,
        pg_meta.default.nextval(mgr_migration_id_seq),
        pg_meta.primary_key('mgr_migration_id_pk')]
    module_id: Annotated[
        pg_bigint,
        pg_meta.foreign_key(
            name='mgr_attribute_module_id_fk',
            other_class=mgr_module,
            other_class_column_name='id')]
    executed_at: pg_datetime
    operation: mgr_migration_operation_enum


@valid_pg_definition
class mgr_object_id_seq(pg_bigint, metaclass=pg_sequence):
    pass


@valid_pg_definition
class mgr_object(pg_table):
    id: Annotated[
        pg_bigint,
        pg_meta.default.nextval(mgr_migration_id_seq),
        pg_meta.primary_key('mgr_object_id_pk')]
    oid: Annotated[
        pg_bigint,
        pg_meta.unique_index('mgr_object_unique_oid_ix')]
    schema_name: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_object_unique_qualified_name_uix')]
    name: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_object_unique_qualified_name_uix')]
    comment: Optional[pg_text]


@valid_pg_definition
class mgr_attribute_id_seq(pg_bigint, metaclass=pg_sequence):
    pass


@valid_pg_definition
class mgr_migration_change_type_enum(pg_enum):
    CREATE = 'create'
    DROP = 'drop'
    UPDATE = 'update'


@valid_pg_definition
class mgr_attribute(pg_table):
    id: Annotated[
        pg_bigint,
        pg_meta.primary_key('mgr_attribute_pk'),
        pg_meta.default.nextval(mgr_attribute_id_seq)]
    object_id: Annotated[
        pg_bigint,
        pg_meta.foreign_key(
            name='mgr_attribute_object_id_fk',
            other_class=mgr_object,
            other_class_column_name='id')]
    name: pg_text


@valid_pg_definition
class mgr_object_changelog(pg_table):
    migration_id: Annotated[
        pg_bigint,
        pg_meta.primary_key('mgr_object_changelog_pk'),
        pg_meta.foreign_key(
            name='mgr_object_changelog_migration_id_fk',
            other_class=mgr_migration,
            other_class_column_name='id')]
    object_id: Annotated[
        pg_bigint,
        pg_meta.primary_key('mgr_object_changelog_pk'),
        pg_meta.foreign_key(
            name='mgr_object_changelog_object_id_fk',
            other_class=mgr_object,
            other_class_column_name='id')]
    attribute_id: Annotated[
        Optional[pg_bigint],
        pg_meta.primary_key('mgr_object_changelog_pk'),
        pg_meta.foreign_key(
            name='mgr_object_changelog_attribute_id_fk',
            other_class=mgr_attribute,
            other_class_column_name='id')]
    operation_type: mgr_migration_change_type_enum
    up_operation: pg_text
    down_operation: pg_text
