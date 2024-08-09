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
    mgr_object


@valid_pg_definition
class mgr_sequence(mgr_object):
    id: Annotated[
        pg_bigint,
        pg_meta.primary_key('mgr_sequence_pk')]
    schema: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_sequence_unique_qualified_name_uix')]
    name: Annotated[
        pg_text,
        pg_meta.unique_index('mgr_sequence_unique_qualified_name_uix')]
    max_value: Optional[pg_bigint]
    min_value: Optional[pg_bigint]


# @valid_pg_definition
# class mgr_sequence_changelog(mgr_object_changelog):
#     id: Annotated[
#         pg_bigint,
#         pg_meta.primary_key('mgr_sequence_changelog_pk')]
#     object_id: Annotated[
#         pg_bigint,
#         pg_meta.foreign_key(
#             name='mgr_sequence_changelog_sequence_id_fk',
#             other_class=mgr_sequence,
#             other_class_column_name='id')]
