from pgdriver.definition.build import\
    pg_smallint,\
    pg_bigint,\
    pg_text,\
    pg_double,\
    pg_byte,\
    pg_datetime,\
    pg_time,\
    pg_date,\
    pg_boolean,\
    pg_char,\
    with_pg_check,\
    with_pg_comment,\
    pg_check,\
    pg_comment,\
    pg_default_value,\
    with_pg_default_value
from pgdriver.definition.base.common.flow import\
    FlowEndException,\
    FlowNodeException
from pgdriver.definition.base.common.meta import\
    literal,\
    this,\
    field
import numpy as np


def test_builtin_definition_is_correctly_formed() -> None:
    def test_builtin_definition_inner(builtin: type) -> None:
        assert hasattr(builtin, '__pg_definition')
        definition: dict[str, str] = getattr(builtin, '__pg_definition')()
        assert 'type' in definition
        assert definition['type'] == builtin

    test_builtin_definition_inner(pg_bigint)
    test_builtin_definition_inner(pg_smallint)
    test_builtin_definition_inner(pg_text)
    test_builtin_definition_inner(pg_double)
    test_builtin_definition_inner(pg_byte)
    test_builtin_definition_inner(pg_char)
    test_builtin_definition_inner(pg_datetime)
    test_builtin_definition_inner(pg_time)
    test_builtin_definition_inner(pg_date)
    test_builtin_definition_inner(pg_boolean)


def test_builtin_domain_definition_is_correctly_formed() -> None:
    # CHECK FOR ABSCENCE OF COMMENT
    @with_pg_check(name='domain_greater_than_0', predicate=this() >= literal(0))
    @with_pg_comment('this is a test comment')
    class domain0(pg_smallint):
        pass

    assert hasattr(domain0, '__pg_definition')
    definition: dict[str, str] = getattr(domain0, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain0
    assert 'base_type' in definition
    assert definition['base_type'] == pg_smallint
    assert 'comment' in definition
    assert isinstance(definition['comment'], pg_comment)
    assert definition['comment'].value == 'this is a test comment'
    assert 'check' in definition
    assert definition['check'].name == 'domain_greater_than_0'
    assert str(definition['check']) == '(VALUE >= 0)'

    # CHECK FOR ABSCENCE OF COMMENT
    @with_pg_check(name='domain_greater_than_0', predicate=this() >= literal(0))
    class domain1(pg_smallint):
        pass

    assert hasattr(domain1, '__pg_definition')
    definition: dict[str, str] = getattr(domain1, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain1
    assert 'base_type' in definition
    assert definition['base_type'] == pg_smallint
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert definition['check'].name == 'domain_greater_than_0'
    assert str(definition['check']) == '(VALUE >= 0)'

    # CHECK FOR ABSENCE OF COMMENT
    @with_pg_check(name='domain_greater_than_0', predicate=this() >= literal(0))
    class domain2(pg_smallint):
        pass

    assert hasattr(domain2, '__pg_definition')
    definition: dict[str, str] = getattr(domain2, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain2
    assert 'base_type' in definition
    assert definition['base_type'] == pg_smallint
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert definition['check'].name == 'domain_greater_than_0'
    assert str(definition['check']) == '(VALUE >= 0)'

    # CHECK FOR ABSENCE OF CHECK
    @with_pg_comment('test comment')
    class domain3(pg_smallint):
        pass

    assert hasattr(domain3, '__pg_definition')
    definition: dict[str, str] = getattr(domain3, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain3
    assert 'base_type' in definition
    assert definition['base_type'] == pg_smallint
    assert 'comment' in definition
    assert isinstance(definition['comment'], pg_comment)
    assert definition['comment'].value == 'test comment'
    assert 'check' in definition
    assert definition['check'] is None

    # CHECK FOR ABSENCE OF COMMENT CHECK AND COMMENT
    class domain4(pg_smallint):
        pass

    assert hasattr(domain4, '__pg_definition')
    definition: dict[str, str] = getattr(domain4, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain4
    assert 'base_type' in definition
    assert definition['base_type'] == pg_smallint
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert definition['check'] is None


def test_builtin_domain_inherits_check_constraint() -> None:
    @with_pg_check(name='domain_greater_than_0', predicate=this() >= literal(0))
    class domain0(pg_smallint):
        pass

    class domain1(domain0):
        pass

    try:
        domain1(-1)
        # no pasa la prueba
        assert False
    except ValueError as e:
        # luego el ValueError sera reemplazado por un error de pydantic
        assert str(e) == 'domain_greater_than_0: constraint validation failed for value "-1"'

    assert hasattr(domain1, '__pg_definition')
    definition: dict[str, str] = getattr(domain1, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain1
    assert 'base_type' in definition
    assert definition['base_type'] == domain0
    assert 'comment' in definition
    assert definition['comment'] is None
    assert definition['check'] is None


def test_builtin_domain_merges_inherited_check_constraint() -> None:
    @with_pg_check(name='domain_greater_than_0', predicate=this() >= literal(0))
    class domain0(pg_smallint):
        pass

    @with_pg_check(name='domain_less_than_5', predicate=this() <= literal(5))
    class domain1(domain0):
        pass

    try:
        domain1(-1)
        # no pasa la prueba
        assert False
    except ValueError as e:
        # luego el ValueError sera reemplazado por un error de pydantic
        assert str(e) == 'domain_greater_than_0: constraint validation failed for value "-1"'

    try:
        domain1(6)
        # no pasa la prueba
        assert False
    except ValueError as e:
        # luego el ValueError sera reemplazado por un error de pydantic
        assert str(e) == 'domain_less_than_5: constraint validation failed for value "6"'

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
    class domain0(pg_smallint):
        pass

    @with_pg_default_value(2)
    class domain1(domain0):
        pass

    assert hasattr(domain1, '__pg_definition')
    definition: dict[str, str] = getattr(domain1, '__pg_definition')()
    assert 'default_value' in definition
    assert definition['default_value'] is not None
    assert isinstance(definition['default_value'], pg_default_value)
    assert isinstance(definition['default_value'].default, literal)
    assert isinstance(definition['default_value'].default._lit, domain1)
    assert definition['default_value'].default._lit == 2


def test_builtin_timestamp_correctly_instantiated() -> None:
    tm = pg_time('10:50')
    assert str(tm) == '1970-01-01T10:50:00.000000'
    try:
        dt = pg_date('10:50')
        assert False
    except ValueError as e:
        assert str(e) == 'Error parsing datetime string "10:50" at position 2'
    try:
        dt = pg_datetime('10:50')
        assert False
    except ValueError as e:
        assert str(e) == 'Error parsing datetime string "10:50" at position 2'
    dt = pg_date('2020-10-10')
    assert str(dt) == '2020-10-10'
    dt = pg_date('2020-10-10T10:50:00.000')
    assert str(dt) == '2020-10-10'
    tp = pg_datetime('2024-11-22T15:30:00+03:00')
    assert str(tp) == '2024-11-22T12:30:00'


def test_builtin_timestamp_checks() -> None:
    @with_pg_check(name='test_domain0__ge2024',
                   predicate=this() >= literal('2024-10-10T10:20'))
    class domain0(pg_datetime):
        pass
    try:
        domain0('2024-10-09T10:19')
        assert False
    except ValueError as e:
        assert str(e) == 'test_domain0__ge2024: constraint validation failed for value "2024-10-09T10:19"'

    @with_pg_check(name='test_domain0__ge10_10',
                   predicate=this() >= literal('10:10'))
    class domain1(pg_time):
        pass
    try:
        domain1('10:09')
        assert False
    except ValueError as e:
        assert str(e) == 'test_domain0__ge10_10: constraint validation failed for value "1970-01-01T10:09:00.000000"'

    @with_pg_check(name='test_domain0__ge2024',
                   predicate=this() >= literal('2024-10-10'))
    class domain1(pg_date):
        pass
    try:
        domain1('2024-10-09')
        assert False
    except ValueError as e:
        assert str(e) == 'test_domain0__ge2024: constraint validation failed for value "2024-10-09"'


def test_check_respected_when_used_in_ndarray() -> None:
    @with_pg_check(name='domain_greater_than_0', predicate=this() >= literal(0))
    class domain0(pg_smallint):
        pass
    # TODO: when creating an nparray even though its created with domain0 as dtype
    # it falls back to numpy underlying type, branching out the type validations in place.
    # We need to evaluate whats the desired behavior for these instances.
    d = np.array([1, 2, -1], dtype=domain0)
    print(repr(d))
