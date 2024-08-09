from pgdriver.migration.types.diff import\
    mgr_diff_composite_definition,\
    mgr_diff_table_definition,\
    mgr_diff_enum_definition,\
    mgr_diff_domain_definition,\
    mgr_diff_sequence_definition
from pgdriver.definition.build import\
    pg_composite,\
    pg_table,\
    pg_enum,\
    pg_domain,\
    pg_sequence


def get_db_composite_definition(schema_name: str, composite_name: str) -> mgr_diff_composite_definition:
    pass


def get_db_table_definition(schema_name: str, table_name: str) -> mgr_diff_table_definition:
    pass


def get_db_enum_definition(schema_name: str, enum_name: str) -> mgr_diff_enum_definition:
    pass


def get_db_domain_definition(schema_name: str, domain_name: str) -> mgr_diff_domain_definition:
    pass


def get_db_sequence_definition(schema_name: str, sequence_name: str) -> mgr_diff_sequence_definition:
    pass


def get_composite_definition(composite_def: type[pg_composite]) -> mgr_diff_composite_definition:
    pass


def get_table_definition(table_def: type[pg_table]) -> mgr_diff_table_definition:
    pass


def get_enum_definition(enum_def: type[pg_enum]) -> mgr_diff_enum_definition:
    pass


def get_domain_definition(domain_def: type[pg_domain]) -> mgr_diff_domain_definition:
    pass


def get_sequence_definition(sequence_def: type[pg_sequence]) -> mgr_diff_sequence_definition:
    pass
