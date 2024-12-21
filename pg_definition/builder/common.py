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
import os
import re


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
SQLSentenceParams: TypeAlias = tuple[str, list[sql.Identifier],  Union[list[str], dict[str, Any]]]


class GeneratesSQLSentence(ABC):
    @abstractmethod
    def sql_sentence_params(self) -> SQLSentenceParams:
        pass


def load_functions_from_file(
    path: str, schema: str, names: Optional[tuple[str, ...]]
) -> dict[str, str]:
    assert os.path.exists(path)
    res: dict[str, str] = {}
    buf, func_name = [], ''
    stack: list[str] = []
    create_re = r'\s*CREATE\s+OR\s+REPLACE\s+FUNCTION\s*'
    read_func: bool = True
    with open(path, 'r') as fns:
        for line in fns:
            buf.append(line.rstrip())
            if re.match(create_re, line) is not None:
                func_name = re.sub(create_re, '', line)
                func_name = re.sub(r'\s*\(.*\n', '', func_name)
                buf[0] = buf[0].replace(func_name, f'{schema}.{func_name}')
                read_func = func_name in (names if names is not None else (func_name, ))
                if read_func:
                    stack.append(func_name)
            if not read_func:
                buf = []
                continue
            if '$$' in line:
                if len(stack) == 1:
                    # the function started
                    stack.append('$$')
                elif stack[-1] == '$$':
                    # the function finished
                    stack.pop()
                else:
                    raise Exception(f'Invalid definition in file "{path}" stack: {stack}')
            if ';' in line and len(stack) == 1:
                name: str = stack.pop()
                if name not in res:
                    res[name] = ["\n".join(buf).strip()]
                else:
                    res[name].append("\n".join(buf).strip())
                buf = []
    return res
