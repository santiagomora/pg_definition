from __future__ import\
    annotations
import pgdriver as pg
from typing_extensions import\
    Annotated
from enum import\
    auto


class mgr_migration_revision_seq(pg.int8_sequence):
    pass


class mgr_migration(pg.table):
    id: Annotated[
        pg.int8,
        pg.primary_key(name='mgr_migration_id_pk')]
    datafix_file_name: pg.text
    migration_file_name: pg.text
    created_at: pg.timestamptz
    depends_on_id: Annotated[
        pg.int8,
        pg.foreign_key(name='mgr_migration_dependency_pk',
                       other_class=mgr_migration,
                       other_class_column_name='id')]


class mgr_migration_execution_type(pg.enums):
    up = auto()
    down = auto()


class mgr_migration_execution(pg.table):
    migration_id: Annotated[
        pg.int8,
        pg.foreign_key(name='mgr_migration_execution_migration_id_pk',
                       other_class=mgr_migration,
                       other_class_column_name='id')]
    executed_at: pg.timestamptz
    type: mgr_migration_execution_type
    comment: pg.text
