from typing import\
    Generator
from abc import\
    ABC
from .backend.types import\
    mgr_migration,\
    mgr_migration_execution,\
    mgr_migration_execution_type,\
    mgr_migration_revision_seq,\
    mgr_migration_id_seq
from .backend.functions import\
    mgr_generate_migration,\
    mgr_get_last_executed_migration_revision,\
    mgr_get_last_generated_migration_revision,\
    mgr_get_revision_range,\
    mgr_register_execution,\
    mgr_get_migration_by_id
from ..extension import\
    Extension


__all__ = ['migration_extension']


class _MigrationExtension(Extension):
    def tables(self) -> Generator[type, None, None]:
        yield mgr_migration
        yield mgr_migration_execution

    def enums(self) -> Generator[type, None, None]:
        yield mgr_migration_execution_type

    def sequences(self) -> Generator[type, None, None]:
        yield mgr_migration_revision_seq
        yield mgr_migration_id_seq

    def functions(self) -> Generator[type, None, None]:
        yield mgr_generate_migration
        yield mgr_get_last_executed_migration_revision
        yield mgr_get_last_generated_migration_revision
        yield mgr_get_revision_range
        yield mgr_register_execution
        yield mgr_get_migration_by_id


# schema is determined through configuration files, for now its hardcoded
migration_extension = _MigrationExtension('test')
