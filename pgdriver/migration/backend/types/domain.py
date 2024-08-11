from pgdriver.definition.build import\
    pg_bigint,\
    pg_text
from pgdriver.definition.meta import\
    pg_meta
from pgdriver.definition.registry import\
    valid_pg_definition
from typing_extensions import\
    Annotated
from pgdriver.migration.backend.types import\
    mgr_object


@valid_pg_definition
class mgr_domain(mgr_object):
    id: Annotated[
        pg_bigint,
        pg_meta.primary_key('mgr_domain_pk')]
    check_constraint: pg_text
    schema: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_domain_unique_qualified_name_uix')]
    name: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_domain_unique_qualified_name_uix')]
    type_name: pg_text


# @valid_pg_definition
# class mgr_domain_changelog(mgr_object_changelog):
#     id: Annotated[
#         pg_bigint,
#         pg_meta.primary_key('mgr_domain_changelog_pk')]
#     object_id: Annotated[
#         pg_bigint,
#         pg_meta.foreign_key(
#             name='mgr_domain_changelog_domain_id_fk',
#             other_class=mgr_domain,
#             other_class_column_name='id')]

