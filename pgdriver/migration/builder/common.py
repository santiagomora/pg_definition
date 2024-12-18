from typing import\
    Any,\
    Optional,\
    TypeAlias
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


class Builder(ABC):
    pass


class WrapsComponent:
    def __init__(self, component: Component) -> None:
        self.component = component


# string con la sentencia, una lista de identificadores, una lista de parametros
SQLSentenceParams: TypeAlias = tuple[str, list[sql.Identifier], list[str]]


class GeneratesSQLSentence(ABC):
    @abstractmethod
    def sql_sentence_params(self) -> SQLSentenceParams:
        pass
