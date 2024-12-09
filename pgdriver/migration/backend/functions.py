import pgdriver as pg
from .types import\
    mgr_migration_execution_type,\
    mgr_migration
from typing import\
    Optional


class mgr_generate_migration(pg.single_result_function[mgr_migration]):
    p_with_datafix: pg.boolean


class mgr_get_last_executed_migration_revision(pg.single_result_function[pg.bigint]):
    pass


class mgr_get_last_generated_migration_revision(pg.single_result_function[pg.bigint]):
    pass


class mgr_get_revision_range(pg.set_returning_function[pg.bigint]):
    p_from: pg.bigint
    p_to: pg.bigint


class mgr_register_execution(pg.perform_function):
    p_migration: mgr_migration
    p_type: mgr_migration_execution_type
    p_comment: Optional[pg.text]


class mgr_get_migration_by_id(pg.single_result_function[mgr_migration]):
    p_id: pg.bigint
