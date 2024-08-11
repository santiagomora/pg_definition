from pgdriver.definition.build import\
    pg_bigint,\
    pg_text,\
    pg_int
from pgdriver.definition.meta import\
    pg_meta
from pgdriver.definition.registry import\
    valid_pg_definition
from typing_extensions import\
    Annotated
from pgdriver.migration.backend.types import\
    mgr_object,\
    mgr_attribute


@valid_pg_definition
class mgr_enum(mgr_object):
    id: Annotated[
        pg_bigint,
        pg_meta.primary_key('mgr_enum_pk')]
    schema: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_enum_unique_qualified_name_uix')]
    name: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_enum_unique_qualified_name_uix')]


# @valid_pg_definition
# class mgr_enum_changelog(mgr_object_changelog):
#     id: Annotated[
#         pg_bigint,
#         pg_meta.primary_key('mgr_enum_changelog_pk')]
#     object_id: Annotated[
#         pg_bigint,
#         pg_meta.foreign_key(
#             name='mgr_enum_changelog_enum_id_fk',
#             other_class=mgr_enum,
#             other_class_column_name='id')]


@valid_pg_definition
class mgr_enum_value(mgr_attribute):
    id: Annotated[
        pg_bigint,
        pg_meta.primary_key('mgr_enum_value_pk')]
    name: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_table_unique_index_name_object_id_uix')]
    object_id: Annotated[
        pg_bigint,
        pg_meta.unique_index('mgr_table_unique_index_name_object_id_uix'),
        pg_meta.foreign_key(
            name='mgr_enum_value_object_id_fk',
            other_class=mgr_enum,
            other_class_column_name='id')]
    order: pg_int
    name: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_table_unique_index_name_object_id_uix')]

