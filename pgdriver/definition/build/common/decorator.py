

def with_pg_check(check: pg_meta.check) -> Callable[type, type]:
    """
    Checks can be inserted into domains
    """

    def inject_check(wrapped_cls: type) -> type:
        if not isinstance(wrapped_cls, pg_domain):
            raise Exception('Check decorators can only be applied on domains.')

        clsname: str = wrapped_cls.__name__
        bases: tuple[type] = extract_by_instance_type_from_inherited_classes(wrapped_cls)
        clsdict = dict(wrapped_cls.__dict__)

        def __new__(cls, *args, **kwargs):
            check.predicate.check_value(args[0], clsdict)
            return bases[0].__new__(bases[0], *args)

        @classmethod
        def __get_pydantic_core_schema__(cls, *args, **kwargs) -> core_schema.CoreSchema:
            return check._check__get_pydantic_core_schema__(*args, **kwargs)

        @classmethod
        def __pg_check(cls) -> pg_meta.check:
            return check

        return type(clsname, bases, clsdict | {
            '__new__': __new__,
            '__get_pydantic_core_schema__': __get_pydantic_core_schema__,
            '__pg_check': __pg_check})
    return inject_check


def with_pg_comment(comment: pg_meta.comment) -> Callable[type, type]:
    """
    Comments can be inserted into all types
    """

    def inject_comment(wrapped_cls: type) -> type:
        bases: tuple[type] = extract_by_instance_type_from_inherited_classes(wrapped_cls)

        @classmethod
        def __pg_comment(cls) -> pg_meta.comment:
            return comment

        return type(wrapped_cls.__name__, bases, dict(wrapped_cls.__dict__) | {
            '__pg_comment': __pg_comment})
    return inject_comment
