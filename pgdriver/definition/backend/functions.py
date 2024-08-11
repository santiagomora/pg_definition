from pgdriver.definition.backend.base import\
    def_composite_definition,\
    def_table_definition,\
    def_enum_definition,\
    def_domain_definition,\
    def_sequence_definition
from pgdriver.definition.extraction.base import\
    pg_composite_definition,\
    pg_table_definition,\
    pg_enum_definition,\
    pg_domain_definition,\
    pg_sequence_definition
from typing import\
    Optional


async def get_db_composite_definition(schema_name: str, composite_name: str) -> Optional[def_composite_definition]:
    pass


async def get_db_table_definition(schema_name: str, table_name: str) -> Optional[def_table_definition]:
    pass


async def get_db_enum_definition(schema_name: str, enum_name: str) -> Optional[def_enum_definition]:
    pass


async def get_db_domain_definition(schema_name: str, domain_name: str) -> Optional[def_domain_definition]:
    pass


async def get_sequence_definition(schema_name: str, sequence_name: str) -> Optional[def_sequence_definition]:
    pass


def as_composite_definition(def_composite: def_composite_definition) -> pg_composite_definition:
    pass


def as_table_definition(def_table: def_table_definition) -> pg_table_definition:
    pass


def as_enum_definition(def_enum: def_enum_definition) -> pg_enum_definition:
    pass


def as_domain_definition(def_domain: def_domain_definition) -> pg_domain_definition:
    pass


def as_sequence_definition(def_sequence: def_sequence_definition) -> pg_sequence_definition:
    pass


def extract_db_definition(schema_name: str, name: str) -> Any:
    pass
