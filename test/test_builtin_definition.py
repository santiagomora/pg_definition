from pgdriver import\
    smallint,\
    bigint,\
    text,\
    double,\
    byte,\
    timestamptz,\
    timetz,\
    date,\
    boolean,\
    char,\
    with_check,\
    with_comment,\
    check,\
    comment,\
    default_value,\
    with_default_value,\
    FlowEndException,\
    FlowNodeException,\
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

    test_builtin_definition_inner(bigint)
    test_builtin_definition_inner(smallint)
    test_builtin_definition_inner(text)
    test_builtin_definition_inner(double)
    test_builtin_definition_inner(byte)
    test_builtin_definition_inner(char)
    test_builtin_definition_inner(timestamptz)
    test_builtin_definition_inner(timetz)
    test_builtin_definition_inner(date)
    test_builtin_definition_inner(boolean)


def test_builtin_domain_definition_is_correctly_formed() -> None:
    # CHECK FOR ABSCENCE OF COMMENT
    @with_check(name='domain_greater_than_0', predicate=this() >= literal(0))
    @with_comment('this is a test comment')
    class domain0(smallint):
        pass

    assert hasattr(domain0, '__pg_definition')
    definition: dict[str, str] = getattr(domain0, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain0
    assert 'base_type' in definition
    assert definition['base_type'] == smallint
    assert 'comment' in definition
    assert isinstance(definition['comment'], comment)
    assert definition['comment'].value == 'this is a test comment'
    assert 'check' in definition
    assert definition['check'].name == 'domain_greater_than_0'
    assert str(definition['check']) == '(VALUE >= 0)'

    # CHECK FOR ABSCENCE OF COMMENT
    @with_check(name='domain_greater_than_0', predicate=this() >= literal(0))
    class domain1(smallint):
        pass

    assert hasattr(domain1, '__pg_definition')
    definition: dict[str, str] = getattr(domain1, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain1
    assert 'base_type' in definition
    assert definition['base_type'] == smallint
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert definition['check'].name == 'domain_greater_than_0'
    assert str(definition['check']) == '(VALUE >= 0)'

    # CHECK FOR ABSENCE OF COMMENT
    @with_check(name='domain_greater_than_0', predicate=this() >= literal(0))
    class domain2(smallint):
        pass

    assert hasattr(domain2, '__pg_definition')
    definition: dict[str, str] = getattr(domain2, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain2
    assert 'base_type' in definition
    assert definition['base_type'] == smallint
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert definition['check'].name == 'domain_greater_than_0'
    assert str(definition['check']) == '(VALUE >= 0)'

    # CHECK FOR ABSENCE OF CHECK
    @with_comment('test comment')
    class domain3(smallint):
        pass

    assert hasattr(domain3, '__pg_definition')
    definition: dict[str, str] = getattr(domain3, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain3
    assert 'base_type' in definition
    assert definition['base_type'] == smallint
    assert 'comment' in definition
    assert isinstance(definition['comment'], comment)
    assert definition['comment'].value == 'test comment'
    assert 'check' in definition
    assert definition['check'] is None

    # CHECK FOR ABSENCE OF COMMENT CHECK AND COMMENT
    class domain4(smallint):
        pass

    assert hasattr(domain4, '__pg_definition')
    definition: dict[str, str] = getattr(domain4, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain4
    assert 'base_type' in definition
    assert definition['base_type'] == smallint
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert definition['check'] is None


def test_builtin_domain_inherits_check_constraint() -> None:
    @with_check(name='domain_greater_than_0', predicate=this() >= literal(0))
    class domain0(smallint):
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
    @with_check(name='domain_greater_than_0', predicate=this() >= literal(0))
    class domain0(smallint):
        pass

    @with_check(name='domain_less_than_5', predicate=this() <= literal(5))
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
    class domain0(smallint):
        pass

    @with_default_value(2)
    class domain1(domain0):
        pass

    assert hasattr(domain1, '__pg_definition')
    definition: dict[str, str] = getattr(domain1, '__pg_definition')()
    assert 'default_value' in definition
    assert definition['default_value'] is not None
    assert isinstance(definition['default_value'], default_value)
    assert isinstance(definition['default_value'].default, literal)
    assert isinstance(definition['default_value'].default._lit, domain1)
    assert definition['default_value'].default._lit == 2


def test_builtin_timestamptz_correctly_instantiated() -> None:
    tm = timetz('10:50')
    assert str(tm) == '10:50:00'
    try:
        dt = date('10:50')
        assert False
    except ValueError as e:
        assert str(e) == 'Invalid isoformat string: \'10:50\''
    try:
        dt = timestamptz('10:50')
        assert False
    except ValueError as e:
        assert str(e) == 'Invalid isoformat string: \'10:50\''
    dt = date('2020-10-10')
    assert str(dt) == '2020-10-10'
    dt = date('2020-10-10')
    assert str(dt) == '2020-10-10'
    tp = timestamptz('2024-11-22 15:30:00+03:00')
    assert str(tp) == '2024-11-22 15:30:00'


def test_builtin_timestamptz_checks() -> None:
    @with_check(name='test_domain0__ge2024',
                   predicate=this() >= literal('2024-10-10T10:20'))
    class domain0(timestamptz):
        pass
    try:
        domain0('2024-10-09T10:19')
        assert False
    except ValueError as e:
        assert str(e) == 'test_domain0__ge2024: constraint validation failed for value "2024-10-09 10:19:00"'

    @with_check(name='test_domain0__ge10_10',
                   predicate=this() >= literal('10:10'))
    class domain1(timetz):
        pass
    try:
        domain1('10:09')
        assert False
    except ValueError as e:
        assert str(e) == 'test_domain0__ge10_10: constraint validation failed for value "10:09:00"'

    @with_check(name='test_domain0__ge2024',
                   predicate=this() >= literal('2024-10-10'))
    class domain1(date):
        pass
    try:
        domain1('2024-10-09')
        assert False
    except ValueError as e:
        assert str(e) == 'test_domain0__ge2024: constraint validation failed for value "2024-10-09"'


def test_check_respected_when_used_in_ndarray() -> None:
    @with_check(name='domain_greater_than_0', predicate=this() >= literal(0))
    class domain0(smallint):
        pass
    # TODO: when creating an nparray even though its created with domain0 as dtype
    # it falls back to numpy underlying type, branching out the type validations in place.
    # We need to evaluate whats the desired behavior for these instances.
    d = np.array([1, 2, -1], dtype=domain0)
    print(repr(d))
