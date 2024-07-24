from pgdriver.definition.tools.metadata import\
    pg_comment_meta,\
    pg_check_meta
from typing import\
    Callable
from typing import\
    Any
from pydantic_core import\
    core_schema,\
    SchemaValidator
from pydantic.annotated_handlers import\
    GetCoreSchemaHandler
from pgdriver.definition.tools.inspection import\
    extract_by_instance_type_from_inherited_classes
from pgdriver.definition.tools import\
    pg_domain,\
    pg_table,\
    pg_unique_index,\
    pg_foreign_key,\
    pg_index,\
    pg_primary_key


def with_pg_comment(comment: pg_comment_meta) -> Callable[type, type]:
    """
    Comments can be inserted into composites, domains, or enums
    """
    def inject_comment(wrapped_cls: type) -> type:
        bases: tuple[type] = extract_by_instance_type_from_inherited_classes(wrapped_cls)

        @classmethod
        def __pg_get_comment(cls) -> pg_comment_meta:
            return comment

        return type(wrapped_cls.__name__, bases, dict(wrapped_cls.__dict__) | {
            '__pg_get_comment': __pg_get_comment})
    return inject_comment


def with_pg_check(check: pg_check_meta) -> Callable[type, type]:
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
            return check._pg_check_meta__get_pydantic_core_schema__(*args, **kwargs)

        @classmethod
        def __pg_get_check(cls) -> pg_check_meta:
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


def is_domain(cls: type):
    bases: tuple[type] = extract_by_instance_type_from_inherited_classes(cls)
    return pg_domain(cls.__name__, bases, dict(cls.__dict__))


def with_pg_foreign_key(fk: pg_foreign_key) -> Callable[type, type]:
    def inject_fk(wrapped_cls: type) -> type:
        if not issubclass(wrapped_cls, pg_table):
            raise Exception('Class {wrapped_cls.__name__} must be a subclass of pg_table to decorate with "with_pg_foreign_key".')
        bases: tuple[type] = extract_by_instance_type_from_inherited_classes(wrapped_cls)

        @classmethod
        def __pg_get_foreign_key(cls) -> pg_foreign_key:
            return fk

        return type(wrapped_cls.__name__, bases, dict(wrapped_cls.__dict__) | {
            '__pg_get_foreign_key': __pg_get_foreign_key})
    return inject_fk


def with_pg_index(ix: pg_index) -> Callable[type, type]:
    def inject_ix(wrapped_cls: type) -> type:
        if not issubclass(wrapped_cls, pg_table):
            raise Exception('Class {wrapped_cls.__name__} must be a subclass of pg_table to decorate with "with_pg_index".')
        bases: tuple[type] = extract_by_instance_type_from_inherited_classes(wrapped_cls)

        @classmethod
        def __pg_get_index(cls) -> pg_index:
            return ix

        return type(wrapped_cls.__name__, bases, dict(wrapped_cls.__dict__) | {
            '__pg_get_index': __pg_get_index})
    return inject_ix


def with_pg_unique_index(uix: pg_unique_index) -> Callable[type, type]:
    def inject_uix(wrapped_cls: type) -> type:
        if not issubclass(wrapped_cls, pg_table):
            raise Exception(f'Class {wrapped_cls.__name__} must be a subclass of pg_table to decorate with "with_pg_unique_index".')
        bases: tuple[type] = extract_by_instance_type_from_inherited_classes(wrapped_cls)

        @classmethod
        def __pg_get_unique_index(cls) -> pg_unique_index:
            return uix

        return type(wrapped_cls.__name__, bases, dict(wrapped_cls.__dict__) | {
            '__pg_get_unique_index': __pg_get_unique_index})
    return inject_uix


def with_pg_primary_key(pk: pg_primary_key) -> Callable[type, type]:
    def inject_pk(wrapped_cls: type) -> type:
        if not issubclass(wrapped_cls, pg_table):
            raise Exception(f'Class {wrapped_cls.__name__} must be a subclass of pg_table to decorate with "with_pg_primary_key".')
        bases: tuple[type] = extract_by_instance_type_from_inherited_classes(wrapped_cls)

        @classmethod
        def __pg_get_primary_key(cls) -> pg_primary_key:
            return pk

        return type(wrapped_cls.__name__, bases, dict(wrapped_cls.__dict__) | {
            '__pg_get_primary_key': __pg_get_primary_key})
    return inject_pk
