from pgdriver.definition.build import\
    pg_bigint,\
    pg_meta,\
    pg_text
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
class mgr_composite(mgr_object):
    id: Annotated[
        pg_bigint,
        pg_meta.primary_key('mgr_composite_pk')]
    check_constraint: pg_text
    schema: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_composite_unique_qualified_name_uix')]
    name: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_composite_unique_qualified_name_uix')]


@valid_pg_definition
class mgr_composite_attribute(mgr_attribute):
    id: Annotated[
        pg_bigint,
        pg_meta.primary_key('mgr_composite_attribute_pk')]
    name: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_composite_attribute_name_object_id_uix')]
    object_id: Annotated[
        pg_bigint,
        pg_meta.foreign_key(
            name='mgr_composite_attribute_object_id_fk',
            other_class=mgr_composite,
            other_class_column_name='id')]
    check: Optional[pg_text]
    comment: Optional[pg_text]
    type_name: pg_text


# @valid_pg_definition
# class mgr_composite_changelog(mgr_object_changelog):
#     migration_id: Annotated[
#         pg_bigint,
#         pg_meta.primary_key('mgr_composite_changelog_pk'),
#         pg_meta.foreign_key(
#             name='mgr_composite_changelog_migration_id_fk',
#             other_class=mgr_migration,
#             other_class_column_name='id')]
#     object_id: Annotated[
#         pg_bigint,
#         pg_meta.primary_key('mgr_composite_changelog_pk'),
#         pg_meta.foreign_key(
#             name='mgr_composite_changelog_object_id_fk',
#             other_class=mgr_composite,
#             other_class_column_name='id')]
#     attribute_id: Annotated[
#         Optional[pg_bigint],
#         pg_meta.primary_key('mgr_composite_changelog_pk'),
#         pg_meta.foreign_key(
#             name='mgr_composite_changelog_attribute_id_fk',
#             other_class=mgr_attribute,
#             other_class_column_name='id')]
