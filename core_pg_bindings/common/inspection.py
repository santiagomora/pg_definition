from typing import\
    Generator,\
    TextIO,\
    TypeAlias,\
    Union
from types import\
    ModuleType
import re
from pydantic.fields import\
    FieldInfo
from psycopg import\
    sql


def extract_definition_fields(cls: type) -> Generator[tuple[str, FieldInfo], None, None]:
    """
    Exclude inherited fields and yield only those fields defined as table 
    attributes directly. Considerations:
    - Child class can redefine parent attribute, changes wont be detected unless
    type or metadata are modified.
    """
    for field_name, info in cls.model_fields.items():
        yield field_name, info
    # return
    # direct_fields: dict[str, FieldInfo] = set(cls.model_fields.keys())
    # for icls in cls.__bases__:
    #     for inherited_field_name in icls.model_fields:
    #         if inherited_field_name in direct_fields:
    #             # if FieldInfo has not changed it means that the field is inherited
    #             # so we must remove it. Otherwise the field is inherited and overriden
    #             # in cls. It doesnt make sense to declare the field exactly as is in child
    #             # model
    #             if DeepDiff(icls.model_fields[inherited_field_name], cls.model_fields[inherited_field_name]) == {}:
    #                 direct_fields.remove(inherited_field_name)
    # for field_name in direct_fields:
    #     yield (field_name, cls.model_fields[field_name])

# def extract_definition_fields(cls: type) -> Generator[tuple[str, type], None, None]:
#     """
#     Exclude inherited fields and yield only those fields defined as table 
#     attributes directly. Considerations:
#     - Child class can redefine parent attribute, changes wont be detected unless
#     type or metadata are modified.
#     """
#     field_names = cls._cpp_field_names
#     field_types = cls._cpp_field_types
#     for ix in range(0, len(field_names)):
#         yield field_names[ix], field_types[ix].get_py_cls(field_types[ix].qualified_name)


def check_tp_is_domain(tp: type) -> bool:
    if not (hasattr(tp, '_postgres_definition') and 'base_type' in tp._postgres_definition):
        raise TypeError(f'Type {tp} must be a domain.')


def check_tp_is_not_domain(tp: type) -> bool:
    if hasattr(tp, '_postgres_definition') and 'base_type' in tp._postgres_definition:
        raise TypeError(f'Type {tp} must not be a domain.')


def load_functions_from_file(
    into: dict[str, dict[str, str]], fns: TextIO, schema: str, names: tuple[str, ...] = None
) -> None:
    buf, func_name = [], ''
    stack: list[str] = []
    params_stack: list[str] = []
    create_re = r'\s*CREATE\s+OR\s+REPLACE\s+FUNCTION\s*'
    read_func: bool = True
    read_func_name: bool = False
    params_str: str = ''
    for line in fns:
        buf.append(line.rstrip())
        if re.match(create_re, line) is not None:
            func_name = re.sub(create_re, '', line)
            func_name = re.sub(r'\s*\(.*\n', '', func_name)
            buf[0] = buf[0].replace(func_name, f'{schema}.{func_name}')
            read_func = func_name in (names if names is not None else (func_name, ))
            read_func_name = read_func
            if read_func:
                stack.append(func_name)
        if read_func_name:
            if '(' in line:
                if ')' in line:
                    params_str = re.search(r'\(.*\)', line).group(0)
                    read_func_name = False
                    params_stack = []
                else:
                    params_stack.append(re.search(r'\(.*', line).group(0))
            elif ')' in line:
                if len(params_stack) > 0:
                    params_stack.append(re.search(r'.*\)', line).group(0))
                else:
                    raise Exception(f'No opening parentheses at function declaration: {func_name}')
                params_str = ''.join(params_stack)
                read_func_name = False
                params_stack = []
            else:
                params_stack.append(line.rstrip('\n'))
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
                raise Exception(f'function doesnt exist: {stack}')
        if ';' in line and len(stack) == 1:
            name: str = stack.pop()
            fn = "\n".join(buf).strip()
            params_str = re.sub(r'((\(\s*)|(\s*\))|\n)', '', params_str)
            params_str = re.sub(r'\s+', ' ', params_str)
            if name not in into:
                into[name] = {params_str: fn}
            else:
                if params_str not in into[name]:
                    into[name][params_str] = fn
                else:
                    raise Exception(f'Invalid function definition "{read_func}", overload "{params_str}" declared more than once')
            buf = []

