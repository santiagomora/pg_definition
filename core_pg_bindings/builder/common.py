from typing import\
    Any,\
    Optional,\
    TypeAlias,\
    Union
from abc import\
    abstractmethod,\
    ABC
from psycopg import\
    sql


class Component:
    def __init__(
        self, name: str, parent: Optional['Component'] = None,
        definition: Optional[dict[str, Any]] = None
    ) -> None:
        self.name = name
        self.parent = parent
        self.definition = definition

    def __repr__(self):
        return f'{self.__class__.__qualname__}({self.name})'


class Builder(ABC):
    pass


class WrapsComponent:
    def __init__(self, component: Component) -> None:
        self.component = component


# string con la sentencia, una lista de identificadores, una lista de parametros
SQLSentenceParams: TypeAlias = tuple[str, list[sql.Identifier],  Union[list[str], dict[str, Any]]]


class GeneratesSQLSentence(ABC):
    @abstractmethod
    def sql_sentence_params(self) -> SQLSentenceParams:
        pass

    @abstractmethod
    def is_opposite(self, other: 'GeneratesSQLSentence') -> bool:
        pass


class Sentence(WrapsComponent, GeneratesSQLSentence):
    def __repr__(self):
        return f'{self.__class__.__name__}({repr(self.component)})'
