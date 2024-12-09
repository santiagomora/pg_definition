from pgdriver.migration import\
    sql_builder
from typing import\
    Optional


DEPENDS_ON: Optional[int] = {depends_on}
MIGRATION_ID: int = {migration_id}
DATAFIX_ID: Optional[int] = {datafix_id}

# NOTE:      These functions are designed to yield a builder that
#            holds all the operations that the migration is 
#            set to perform to update the postgres objects.


def up() -> None:
    pass


def down() -> None:
    pass
