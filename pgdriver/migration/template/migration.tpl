import pgdriver.migration.builder\
    as bd
from typing import\
    Optional,\
    Generator
from enum import\
    Enum


class preconditions(Enum):
    pass


class postconditions(Enum):
    pass


# This is a list of the postconditions enforced by other migrations
DEPENDS_ON: Optional[list[int]] = {depends_on}
MIGRATION_ID: int = {migration_id}
DATAFIX_ID: Optional[int] = {datafix_id}

# NOTE:      These functions are designed to yield a builder that
#            holds all the operations that the migration is 
#            set to perform to update the postgres objects.


def up() -> Generator[bd.SQLSentenceParams, None, None]:
    pass


def down() -> Generator[bd.SQLSentenceParams, None, None]:
    pass
