import pg_definition as pg
import base_types as bt
# import numpy as np


def test_builtin_definition_is_correctly_formed() -> None:
    def test_builtin_definition_inner(builtin: type) -> None:
        assert hasattr(builtin, '_postgres_definition')
        definition: dict[str, str] = builtin._postgres_definition
        assert 'type' in definition
        assert definition['type'] == builtin

    test_builtin_definition_inner(pg.catalog.int8)
    test_builtin_definition_inner(pg.catalog.int2)
    test_builtin_definition_inner(pg.catalog.text)
    test_builtin_definition_inner(pg.catalog.float8)
    # test_builtin_definition_inner(pg.bytea)
    test_builtin_definition_inner(pg.catalog.int1)
    test_builtin_definition_inner(pg.catalog.timestamptz)
    # test_builtin_definition_inner(pg.timetz)
    test_builtin_definition_inner(pg.catalog.date)
    test_builtin_definition_inner(pg.catalog.bool)


def test_builtin_domain_definition_is_correctly_formed() -> None:
    @pg.builtin.add_comment(value='this is a test comment')
    @pg.builtin.set_check_constraint(
        name='domain_greater_than_0', constraint=pg.this() >= pg.literal(0))
    class domain0(pg.catalog.int2):
        pass

    assert hasattr(domain0, '_postgres_definition')
    definition: dict[str, str] = domain0._postgres_definition
    assert 'type' in definition
    assert definition['type'] == domain0
    assert 'base_type' in definition
    assert definition['base_type'] == pg.catalog.int2
    assert 'comment' in definition
    assert hasattr(definition['comment'], 'value')
    assert definition['comment'].value == 'this is a test comment'
    assert 'check' in definition
    assert definition['check'].name == 'domain_greater_than_0'
    assert str(definition['check']) == 'VALUE >= 0'

    # CHECK FOR ABSCENCE OF COMMENT
    @pg.builtin.set_check_constraint(
        name='domain_greater_than_0', constraint=pg.this() >= pg.literal(0))
    class domain1(pg.catalog.int2):
        pass

    assert hasattr(domain1, '_postgres_definition')
    definition: dict[str, str] = domain1._postgres_definition
    assert 'type' in definition
    assert definition['type'] == domain1
    assert 'base_type' in definition
    assert definition['base_type'] == pg.catalog.int2
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert definition['check'].name == 'domain_greater_than_0'
    assert str(definition['check']) == 'VALUE >= 0'

    # CHECK FOR ABSENCE OF COMMENT
    @pg.builtin.set_check_constraint(name='domain_greater_than_0', constraint=pg.this() >= pg.literal(0))
    class domain2(pg.catalog.int2):
        pass

    assert hasattr(domain2, '_postgres_definition')
    definition: dict[str, str] = domain2._postgres_definition
    assert 'type' in definition
    assert definition['type'] == domain2
    assert 'base_type' in definition
    assert definition['base_type'] == pg.catalog.int2
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert definition['check'].name == 'domain_greater_than_0'
    assert str(definition['check']) == 'VALUE >= 0'

    # CHECK FOR ABSENCE OF CHECK
    @pg.builtin.add_comment(value='test comment')
    class domain3(pg.catalog.int2):
        pass

    assert hasattr(domain3, '_postgres_definition')
    definition: dict[str, str] = domain3._postgres_definition
    assert 'type' in definition
    assert definition['type'] == domain3
    assert 'base_type' in definition
    assert definition['base_type'] == pg.catalog.int2
    assert 'comment' in definition
    assert hasattr(definition['comment'], 'value')
    assert definition['comment'].value == 'test comment'
    assert 'check' in definition
    assert definition['check'] is None

    # CHECK FOR ABSENCE OF COMMENT CHECK AND COMMENT
    class domain4(pg.catalog.int2):
        pass

    assert hasattr(domain4, '_postgres_definition')
    definition: dict[str, str] = domain4._postgres_definition
    assert 'type' in definition
    assert definition['type'] == domain4
    assert 'base_type' in definition
    assert definition['base_type'] == pg.catalog.int2
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert definition['check'] is None


def test_builtin_domain_inherits_meta_constraint() -> None:
    @pg.builtin.set_check_constraint(
        name='domain_greater_than_0', constraint=pg.this() >= pg.literal(0))
    class domain0(pg.catalog.int2):
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

    assert hasattr(domain1, '_postgres_definition')
    definition: dict[str, str] = domain1._postgres_definition
    assert 'type' in definition
    assert definition['type'] == domain1
    assert 'base_type' in definition
    assert definition['base_type'] == domain0
    assert 'comment' in definition
    assert definition['comment'] is None
    assert definition['check'] is None


def test_builtin_domain_merges_inherited_meta_constraint() -> None:
    @pg.builtin.set_check_constraint(
        name='domain_greater_than_0', constraint=pg.this() >= pg.literal(0))
    class domain0(pg.catalog.int2):
        pass

    @pg.builtin.set_check_constraint(
        name='domain_less_than_5', constraint=pg.this() <= pg.literal(5))
    class domain1(domain0):
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

    assert hasattr(domain1, '_postgres_definition')
    definition: dict[str, str] = domain1._postgres_definition
    assert 'type' in definition
    assert definition['type'] == domain1
    assert 'base_type' in definition
    assert definition['base_type'] == domain0
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert definition['check'].name == 'domain_less_than_5'
    assert str(definition['check']) == 'VALUE <= 5'


def test_builtin_domain_takes_default_value() -> None:
    class domain0(pg.catalog.int2):
        pass

    @pg.builtin.set_default(bt.literal(2))
    class domain1(domain0):
        pass

    assert hasattr(domain1, '_postgres_definition')
    definition: dict[str, str] = domain1._postgres_definition
    assert 'default' in definition
    assert definition['default'] is not bt.Undefined
    print(definition['default'])
    assert isinstance(definition['default'], bt.literal)
    assert isinstance(definition['default'], pg.literal)
    assert isinstance(definition['default']._lit, domain0)
    assert definition['default']._lit == 2


def test_builtin_timestamptz_metas() -> None:
    @pg.builtin.set_check_constraint(
        name='test_domain0__ge2024', constraint=pg.this() >= pg.literal('2024-10-10T10:20'))
    class domain0(pg.catalog.timestamptz):
        pass
    try:
        domain0('2024-10-09T10:19')
        assert False
    except ValueError:
        pass

    @pg.builtin.set_check_constraint(
        name='test_domain0__ge2024', constraint=pg.this() >= pg.literal('2024-10-10'))
    class domain1(pg.date):
        pass
    try:
        domain1('2024-10-09')
        assert False
    except ValueError:
        pass


# def test_check_respected_when_used_in_ndarray() -> None:
#     class domain0(
#         pg.catalog.int2, constraint=pg.check(
#             name='domain_greater_than_0', constraint=pg.this() >= pg.literal(0)
#         )
#     ):
#         pass
#     # TODO: when creating an nparray even though its created with domain0 as dtype
#     # it falls back to numpy underlying type, branching out the type validations in place.
#     # We need to evaluate whats the desired behavior for these instances.
#     d = np.array([1, 2, -1], dtype=domain0)
#     print(repr(d))
