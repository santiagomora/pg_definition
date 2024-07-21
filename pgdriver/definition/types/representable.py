from typing import\
    Optional,\
    TypeVar,\
    Generic,\
    get_args,\
    Any


K = TypeVar('K')


class PGRepresentable(Generic[K]):
    _pg_definition: Optional[K]

    def get_definition(self, name: str) -> Any:
        return getattr(self._pg_definition, name)

    @classmethod
    def get_definition_kind(cls) -> type:
        print(get_args(cls))
        return type(cls._pg_definition)
