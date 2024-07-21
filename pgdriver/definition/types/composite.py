from typing import\
    Optional
from collections import\
    OrderedDict
from .representable import\
    PGRepresentable
from pgdriver.adapt.pydantic import\
    PGBaseModel
from abc import\
    ABC
from .check import\
    PGCheckDefinition


class PGAttributeDefinition:
    pass


class PGCompositeDefinition:
    comment:    Optional[str] = None
    check:      Optional[PGCheckDefinition] = None
    attributes: Optional[OrderedDict[PGAttributeDefinition, None]] = None


class pg_composite(PGBaseModel, PGRepresentable[PGCompositeDefinition], ABC):
    pass


