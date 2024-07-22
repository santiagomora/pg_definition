from pgdriver.definition.types.metadata import\
    pg_comment,\
    pg_check
from typing import\
    Callable
from typing import\
    Any
from pydantic_core import\
    core_schema,\
    SchemaValidator
from pydantic.annotated_handlers import\
    GetCoreSchemaHandler
from pgdriver.definition.inspection import\
    extract_by_instance_type_from_inherited_classes


def with_comment(comment: pg_comment) -> Callable[type, type]:
    """
    Comments can be inserted into composites, domains, or enums
    """
    def inject_comment(wrapped_cls: type) -> type:
        bases: tuple[type] = extract_by_instance_type_from_inherited_classes(wrapped_cls)

        @classmethod
        def __pg_get_comment(cls) -> pg_comment:
            return comment

        return type(wrapped_cls.__name__, bases, dict(wrapped_cls.__dict__) | {
            '__pg_get_comment': __pg_get_comment})
    return inject_comment


def with_check(check: pg_check) -> Callable[type, type]:
    """
    Checks can be inserted into domains or composite types
    """
    def inject_check(wrapped_cls: type) -> type:
        clsname: str = wrapped_cls.__name__
        bases: tuple[type] = extract_by_instance_type_from_inherited_classes(wrapped_cls)
        clsdict = dict(wrapped_cls.__dict__)

        def __new__(cls, *args, **kwargs):
            check.predicate.check_value(args[0], clsdict)
            return bases[0].__new__(bases[0], *args)

        @classmethod
        def __get_pydantic_core_schema__(cls, *args, **kwargs) -> core_schema.CoreSchema:
            return check._pg_check__get_pydantic_core_schema__(*args, **kwargs)

        @classmethod
        def __pg_get_check(cls) -> pg_check:
            return check

        return type(clsname, bases, clsdict | {
            '__new__': __new__,
            '__get_pydantic_core_schema__': __get_pydantic_core_schema__,
            '__pg_get_check': __pg_get_check})
    return inject_check


def with_schema(schema: core_schema.CoreSchema) -> Callable[type, type]:
    def inject_schema(wrapped_cls: type) -> type:
        bases: tuple[type] = extract_by_instance_type_from_inherited_classes(wrapped_cls)

        def __new__(cls, *args, **kwargs):
            validator: SchemaValidator = SchemaValidator(schema)
            validator.validate_python(*args)
            return bases[0].__new__(bases[0], *args, **kwargs)

        @classmethod
        def __get_pydantic_core_schema__(cls, source: type[Any], handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
            return schema

        return type(wrapped_cls.__name__, bases, dict(wrapped_cls.__dict__) | {
            '__new__': __new__,
            '__get_pydantic_core_schema__': __get_pydantic_core_schema__})
    return inject_schema
