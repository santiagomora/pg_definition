from typing import\
    Optional
from .representable import\
    PGRepresentable
from enum import\
    EnumType
from pgdriver.definition.types.metadata import\
    pg_comment


class PGEnumDefinition:
    comment: Optional[pg_comment] = None


class pg_enum(EnumType):
    pass
