import pg_definition as pg
import base_types as bt
# import numpy as np


def test_builtin_definition_is_correctly_formed() -> None:
    def test_builtin_definition_inner(builtin: type) -> None:
        assert hasattr(builtin, '__pg_definition')
        definition: dict[str, str] = getattr(builtin, '__pg_definition')()
        assert 'type' in definition
        assert definition['type'] == builtin

    test_builtin_definition_inner(pg.int8)
    test_builtin_definition_inner(pg.int2)
    test_builtin_definition_inner(pg.text)
    test_builtin_definition_inner(pg.float8)
    # test_builtin_definition_inner(pg.bytea)
    test_builtin_definition_inner(pg.int1)
    test_builtin_definition_inner(pg.timestamptz)
    # test_builtin_definition_inner(pg.timetz)
    test_builtin_definition_inner(pg.date)
    test_builtin_definition_inner(pg.bool)


def test_builtin_domain_definition_is_correctly_formed() -> None:
    @pg.add_comment('this is a test comment')
    class domain0(
        pg.int2, check_predicate=pg.check(
            name='domain_greater_than_0', predicate=pg.this() >= pg.literal(0)
        )
    ):
        pass

    assert hasattr(domain0, '__pg_definition')
    definition: dict[str, str] = getattr(domain0, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain0
    assert 'base_type' in definition
    assert definition['base_type'] == pg.int2
    assert 'comment' in definition
    assert isinstance(definition['comment'], pg.comment)
    assert definition['comment'].value == 'this is a test comment'
    assert 'check' in definition
    assert definition['check'].name == 'domain_greater_than_0'
    assert str(definition['check']) == '(VALUE >= 0)'

    # CHECK FOR ABSCENCE OF COMMENT
    class domain1(
        pg.int2, check_predicate=pg.check(
            name='domain_greater_than_0', predicate=pg.this() >= pg.literal(0)
        )
    ):
        pass

    assert hasattr(domain1, '__pg_definition')
    definition: dict[str, str] = getattr(domain1, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain1
    assert 'base_type' in definition
    assert definition['base_type'] == pg.int2
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert definition['check'].name == 'domain_greater_than_0'
    assert str(definition['check']) == '(VALUE >= 0)'

    # CHECK FOR ABSENCE OF COMMENT
    class domain2(
        pg.int2, check_predicate=pg.check(
            name='domain_greater_than_0', predicate=pg.this() >= pg.literal(0)
        )
    ):
        pass

    assert hasattr(domain2, '__pg_definition')
    definition: dict[str, str] = getattr(domain2, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain2
    assert 'base_type' in definition
    assert definition['base_type'] == pg.int2
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert definition['check'].name == 'domain_greater_than_0'
    assert str(definition['check']) == '(VALUE >= 0)'

    # CHECK FOR ABSENCE OF CHECK
    @pg.add_comment('test comment')
    class domain3(pg.int2):
        pass

    assert hasattr(domain3, '__pg_definition')
    definition: dict[str, str] = getattr(domain3, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain3
    assert 'base_type' in definition
    assert definition['base_type'] == pg.int2
    assert 'comment' in definition
    assert isinstance(definition['comment'], pg.comment)
    assert definition['comment'].value == 'test comment'
    assert 'check' in definition
    assert definition['check'] is None

    # CHECK FOR ABSENCE OF COMMENT CHECK AND COMMENT
    class domain4(pg.int2):
        pass

    assert hasattr(domain4, '__pg_definition')
    definition: dict[str, str] = getattr(domain4, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain4
    assert 'base_type' in definition
    assert definition['base_type'] == pg.int2
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert definition['check'] is None


def test_builtin_domain_inherits_meta_constraint() -> None:
    class domain0(
        pg.int2, check_predicate=pg.check(
            name='domain_greater_than_0', predicate=pg.this() >= pg.literal(0)
        )
    ):
        pass

    class domain1(domain0):
        pass

    try:
        domain1(-1)
        # no pasa la prueba
        assert False
    except ValueError as e:
        pass
        # luego el ValueError sera reemplazado por un error de pydantic

    assert hasattr(domain1, '__pg_definition')
    definition: dict[str, str] = getattr(domain1, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain1
    assert 'base_type' in definition
    assert definition['base_type'] == domain0
    assert 'comment' in definition
    assert definition['comment'] is None
    assert definition['check'] is None


def test_builtin_domain_merges_inherited_meta_constraint() -> None:
    class domain0(
        pg.int2, check_predicate=pg.check(
            name='domain_greater_than_0', predicate=pg.this() >= pg.literal(0)
        )
    ):
        pass

    class domain1(
        domain0, check_predicate=pg.check(
            name='domain_less_than_5', predicate=pg.this() <= pg.literal(5)
        )
    ):
        pass

    try:
        domain1(-1)
        # no pasa la prueba
        assert False
    except ValueError as e:
        # luego el ValueError sera reemplazado por un error de pydantic
        pass

    try:
        domain1(6)
        # no pasa la prueba
        assert False
    except ValueError as e:
        # luego el ValueError sera reemplazado por un error de pydantic
        pass

    assert hasattr(domain1, '__pg_definition')
    definition: dict[str, str] = getattr(domain1, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain1
    assert 'base_type' in definition
    assert definition['base_type'] == domain0
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert definition['check'].name == 'domain_less_than_5'
    assert str(definition['check']) == '(VALUE <= 5)'


def test_builtin_domain_takes_default_value() -> None:
    class domain0(pg.int2):
        pass

    class domain1(domain0, default=bt.literal(2)):
        pass

    assert hasattr(domain1, '__pg_definition')
    definition: dict[str, str] = getattr(domain1, '__pg_definition')()
    assert 'default' in definition
    assert definition['default'] is not bt.Undefined
    print(definition['default'])
    assert isinstance(definition['default'], bt.literal)
    assert isinstance(definition['default'], pg.literal)
    assert isinstance(definition['default']._lit, domain0)
    assert definition['default']._lit == 2


def test_builtin_timestamptz_metas() -> None:
    class domain0(
        pg.timestamptz, check_predicate=pg.check(
            name='test_domain0__ge2024', predicate=pg.this() >= pg.literal('2024-10-10T10:20')
        )
    ):
        pass
    try:
        domain0('2024-10-09T10:19')
        assert False
    except ValueError:
        pass

    class domain1(
        pg.date, check_predicate=pg.check(
            name='test_domain0__ge2024', predicate=pg.this() >= pg.literal('2024-10-10')
        )
    ):
        pass
    try:
        domain1('2024-10-09')
        assert False
    except ValueError:
        pass


# def test_check_respected_when_used_in_ndarray() -> None:
#     class domain0(
#         pg.int2, check_predicate=pg.check(
#             name='domain_greater_than_0', predicate=pg.this() >= pg.literal(0)
#         )
#     ):
#         pass
#     # TODO: when creating an nparray even though its created with domain0 as dtype
#     # it falls back to numpy underlying type, branching out the type validations in place.
#     # We need to evaluate whats the desired behavior for these instances.
#     d = np.array([1, 2, -1], dtype=domain0)
#     print(repr(d))
