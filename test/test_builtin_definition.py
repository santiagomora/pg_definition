from pgdriver.definition.build import\
    pg_smallint,\
    pg_bigint,\
    pg_text,\
    pg_double,\
    pg_bytea,\
    pg_timestamp,\
    pg_timestamptz,\
    pg_time,\
    pg_timetz,\
    pg_date,\
    pg_boolean,\
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
    ge_,\
    le_,\
    literal_


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
    test_builtin_definition_inner(pg_bytea)
    test_builtin_definition_inner(pg_timestamp)
    test_builtin_definition_inner(pg_timestamptz)
    test_builtin_definition_inner(pg_time)
    test_builtin_definition_inner(pg_timetz)
    test_builtin_definition_inner(pg_date)
    test_builtin_definition_inner(pg_boolean)


def test_builtin_domain_detects_incompatible_types_definition() -> None:
    try:
        @with_pg_check(pg_check[pg_text](name='domain_less_than_5',
                                         predicate=le_[pg_text](literal_(5))))
        class domain(pg_smallint):
            pass
    except TypeError as e:
        # error: Optional[FlowNodeException] = e.get_error('builtin-definition-flow',
        #                                                  'builtin-domain-validate-check-constraint-definition-node')
        # assert error is not None
        assert str(e) == "Check definition error: types \
<class 'pgdriver.definition.base.builtin.pg_smallint'> and <class \
'pgdriver.definition.base.builtin.pg_text'> are not compatible"


def test_builtin_domain_definition_is_correctly_formed() -> None:
    # CHECK FOR ABSCENCE OF COMMENT
    @with_pg_check(pg_check[pg_smallint](name='domain_greater_than_0',
                                         predicate=ge_[pg_smallint](literal_(0))))
    @with_pg_comment(pg_comment('this is a test comment'))
    class domain0(pg_smallint):
        pass

    assert hasattr(domain0, '__pg_definition')
    definition: dict[str, str] = getattr(domain0, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain0
    assert 'base_type' in definition
    assert definition['base_type'] == pg_smallint
    assert 'comment' in definition
    assert definition['comment'].value == 'this is a test comment'
    assert 'check' in definition
    assert definition['check'].name == 'domain_greater_than_0'
    assert definition['check'].as_str('VALUE') == '(VALUE >= 0)'

    # CHECK FOR ABSCENCE OF COMMENT
    @with_pg_check(pg_check[pg_smallint](name='domain_greater_than_0',
                                         predicate=ge_[pg_smallint](literal_(0))))
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
    assert definition['check'].as_str('VALUE') == '(VALUE >= 0)'

    # CHECK FOR ABSENCE OF COMMENT
    @with_pg_check(pg_check[pg_smallint](name='domain_greater_than_0',
                                         predicate=ge_[pg_smallint](literal_(0))))
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
    assert definition['check'].as_str('VALUE') == '(VALUE >= 0)'

    # CHECK FOR ABSENCE OF CHECK
    @with_pg_comment(pg_comment('test comment'))
    class domain3(pg_smallint):
        pass

    assert hasattr(domain3, '__pg_definition')
    definition: dict[str, str] = getattr(domain3, '__pg_definition')()
    assert 'type' in definition
    assert definition['type'] == domain3
    assert 'base_type' in definition
    assert definition['base_type'] == pg_smallint
    assert 'comment' in definition
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
    @with_pg_check(pg_check[pg_smallint](name='domain_greater_than_0',
                                         predicate=ge_[pg_smallint](literal_(0))))
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
        assert str(e) == 'domain_greater_than_0: Greater than equal check error: value "-1" is less than "0"'

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
    @with_pg_check(pg_check[pg_smallint](name='domain_greater_than_0',
                                         predicate=ge_[pg_smallint](literal_(0))))
    class domain0(pg_smallint):
        pass

    @with_pg_check(pg_check[pg_smallint](name='domain_less_than_5',
                                         predicate=le_[pg_smallint](literal_(5))))
    class domain1(domain0):
        pass

    try:
        domain1(-1)
        # no pasa la prueba
        assert False
    except ValueError as e:
        # luego el ValueError sera reemplazado por un error de pydantic
        assert str(e) == 'domain_greater_than_0: Greater than equal check error: value "-1" is less than "0"'

    try:
        domain1(6)
        # no pasa la prueba
        assert False
    except ValueError as e:
        # luego el ValueError sera reemplazado por un error de pydantic
        assert str(e) == 'domain_less_than_5: Less than equal check error: value "6" is greater than "5"'

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
    assert definition['check'].as_str('VALUE') == '(VALUE <= 5)'
    assert definition['check']._parent_check is not None
    assert definition['check']._parent_check.name == 'domain_greater_than_0'
    assert definition['check']._parent_check.as_str('VALUE') == '(VALUE >= 0)'


def test_builtin_domain_takes_default_value() -> None:
    class domain0(pg_smallint):
        pass

    @with_pg_default_value(pg_default_value(2))
    class domain1(domain0):
        pass

    assert hasattr(domain1, '__pg_definition')
    definition: dict[str, str] = getattr(domain1, '__pg_definition')()
    assert 'default_value' in definition
    assert definition['default_value'] is not None
    assert definition['default_value'].content == 2
