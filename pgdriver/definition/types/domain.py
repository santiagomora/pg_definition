from typing import\
    Optional,\
    Generic,\
    TypeVar
from .representable import\
    PGRepresentable
from abc import \
    ABC
from .check import\
    PGCheckDefinition


class PGDomainDefinition:
    comment: Optional[str] = None
    check:   Optional[PGCheckDefinition] = None


# ver como hacer porque PGRepresentable depende de un generic tambien
T = TypeVar('T', bound=PGRepresentable)


# hay que tener cuidado porque estos objetos son proxy en realidad
# al igual que los built_in_types
class pg_domain(type):
    pass
