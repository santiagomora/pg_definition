from pgdriver.definition.build import\
    pg_bigint,\
    pg_meta,\
    pg_enum,\
    pg_text,\
    pg_bool
from pgdriver.definition.registry import\
    valid_pg_definition
from typing_extensions import\
    Annotated
from typing import\
    Optional
from pgdriver.migration.backend.types import\
    mgr_object,\
    mgr_attribute


@valid_pg_definition
class mgr_table(mgr_object):
    id: Annotated[
        pg_bigint,
        pg_meta.primary_key('mgr_table_pk')]
    schema: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_table_unique_qualified_name_uix')]
    name: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_table_unique_qualified_name_uix')]


@valid_pg_definition
class mgr_table_column(mgr_attribute):
    id: Annotated[
        pg_bigint,
        pg_meta.primary_key('mgr_table_column_pk')]
    object_id: Annotated[
        pg_bigint,
        pg_meta.foreign_key(
            name='mgr_table_column_object_id_fk',
            other_class=mgr_table,
            other_class_column_name='id')]
    check: Optional[pg_text]
    comment: Optional[pg_text]
    default_value_name: Optional[pg_text]
    default_sequence_name: Optional[pg_text]
    type_name: pg_text


@valid_pg_definition
class mgr_table_foreign_key_action(pg_enum):
    CASCADE = 'CASCADE'
    NO_ACTION = 'NO ACTION'
    SET_DEFAULT = 'SET DEFAULT'
    SET_NULL = 'SET NULL'
    RESTRICT = 'RESTRICT'


@valid_pg_definition
class mgr_table_foreign_key(mgr_attribute):
    id: Annotated[
        pg_bigint,
        pg_meta.primary_key('mgr_table_foreign_key_pk')]
    object_id: Annotated[
        pg_bigint,
        pg_meta.unique_index('mgr_table_foreign_key_name_object_id_class_column_id_uix'),
        pg_meta.foreign_key(
            name='mgr_table_foreign_key_object_id_fk',
            other_class=mgr_table,
            other_class_column_name='id')]
    name: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_table_foreign_key_name_object_id_class_column_id_uix')]
    class_column_id: Annotated[
        pg_bigint,
        pg_meta.unique_index('mgr_table_foreign_key_name_object_id_class_column_id_uix'),
        pg_meta.foreign_key(
            name='mgr_table_foreign_key_other_class_column_id_fk',
            other_class=mgr_table_column,
            other_class_column_name='id')]
    other_class_id: Annotated[
        pg_bigint,
        pg_meta.foreign_key(
            name='mgr_table_foreign_key_other_class_id_fk',
            other_class=mgr_table,
            other_class_column_name='id')]
    other_class_column_id: Annotated[
        pg_bigint,
        pg_meta.foreign_key(
            name='mgr_table_foreign_key_other_class_column_id_fk',
            other_class=mgr_table_column,
            other_class_column_name='id')]
    on_delete: mgr_table_foreign_key_action
    on_update: mgr_table_foreign_key_action


@valid_pg_definition
class mgr_table_index_type(pg_enum):
    BTREE = 'btree'
    HASH = 'hash'
    BRIN = 'brin'
    GIN = 'gin'
    GIST = 'gist'
    SPGIST = 'spgist'


@valid_pg_definition
class mgr_table_index(mgr_attribute):
    id: Annotated[
        pg_bigint,
        pg_meta.primary_key('mgr_table_index_pk')]
    name: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_table_index_name_object_id_uix')]
    object_id: Annotated[
        pg_bigint,
        pg_meta.unique_index('mgr_table_index_name_object_id_uix'),
        pg_meta.foreign_key(
            name='mgr_table_index_table_id_fk',
            other_class=mgr_table,
            other_class_column_name='id')]
    type: mgr_table_index_type
    is_unique: pg_bool


@valid_pg_definition
class mgr_table_primary_key(mgr_attribute):
    id: Annotated[
        pg_bigint,
        pg_meta.primary_key('mgr_table_primary_key_pk')]
    object_id: Annotated[
        pg_bigint,
        pg_meta.unique_index('mgr_table_primary_key_object_id_column_id_name_uix'),
        pg_meta.foreign_key(
            name='mgr_table_primary_key_table_id_fk',
            other_class=mgr_table,
            other_class_column_name='id')]
    name: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_table_primary_key_object_id_column_id_name_uix')]
    column_id: Annotated[
        pg_bigint,
        pg_meta.unique_index('mgr_table_primary_key_object_id_column_id_name_uix'),
        pg_meta.foreign_key(
            name='mgr_table_primary_key_table_column_id_fk',
            other_class=mgr_table,
            other_class_column_name='id')]


# @valid_pg_definition
# class mgr_table_changelog(mgr_object_changelog):
#     id: Annotated[
#         pg_bigint,
#         pg_meta.primary_key('mgr_table_changelog_pk')]
#     object_id: Annotated[
#         pg_bigint,
#         pg_meta.foreign_key(
#             name='mgr_table_changelog_table_id_fk',
#             other_class=mgr_table,
#             other_class_column_name='id')]
