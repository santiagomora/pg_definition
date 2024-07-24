from typing import\
    Optional,\
    TypeVar,\
    Generic,\
    get_args,\
    Any
from collections import\
    OrderedDict


class PGCheckDefinition:
    pass


class PGAttributeDefinition:
    pass


class PGCompositeDefinition:
    comment:    Optional[str] = None
    check:      Optional[PGCheckDefinition] = None
    attributes: Optional[OrderedDict[PGAttributeDefinition, None]] = None


K = TypeVar('K')


class PGRepresentable(Generic[K]):
    _pg_definition: Optional[K]

    def get_definition(self, name: str) -> Any:
        return getattr(self._pg_definition, name)

    @classmethod
    def get_definition_kind(cls) -> type:
        print(get_args(cls))
        return type(cls._pg_definition)


class PGEnumDefinition:
    comment: Optional[pg_comment_meta] = None


class PGCheckDefinition:
    pass


class PGTriggerDefinition:
    pass


class PGIndexDefinition:
    pass


class PGUniqueIndexDefinition:
    pass


class PGColumnDefinition:
    pass


class PGPrimaryKeyDefinition:
    pass


class PGForeignKeyDefinition:
    pass


class PGTableDefinition:
    comment:           Optional[str] = None
    columns:           Optional[OrderedDict[PGColumnDefinition, None]] = None
    indexes:           Optional[dict[str, PGIndexDefinition]] = None
    unique_indexes:    Optional[dict[str, PGUniqueIndexDefinition]] = None
    foreign_keys:      Optional[dict[str, PGForeignKeyDefinition]] = None
    primary_keys:      Optional[dict[str, PGPrimaryKeyDefinition]] = None
    base_tables:       Optional[tuple[type]] = None
    triggers:          Optional[PGTriggerDefinition] = None
