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
    pg_boolean
from pgdriver.definition.base.common.flow import\
    FlowEndException,\
    FlowNodeException
from pgdriver.definition.base.common.meta import\
    pg_type_check,\
    pg_comment,\
    ge_,\
    le_,\
    literal_
from typing import\
    Optional


def test_builtin_definition_is_correctly_formed() -> None:
    def test_builtin_definition_inner(builtin: type) -> None:
        assert hasattr(builtin, '__pg_definition')
        definition: dict[str, str] = getattr(builtin, '__pg_definition')()
        assert 'schema_name' in definition
        assert definition['schema_name'] == 'public'
        assert 'type_name' in definition
        assert definition['type_name'] == builtin.__name__.replace('pg_', '')

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
        class domain(pg_smallint):
            __pg_check: pg_type_check = pg_type_check[pg_text](name='domain_less_than_5',
                                                               predicate=le_[pg_text](literal_(5)))
    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('builtin-definition-flow',
                                                         'builtin-domain-validate-check-constraint-definition-node')
        assert error is not None
        assert str(error) == "Check definition error: types \
<class 'pgdriver.definition.base.builtin.pg_smallint'> and <class \
'pgdriver.definition.base.builtin.pg_text'> are not compatible"


def test_builtin_domain_definition_is_correctly_formed() -> None:
    # CHECK FOR ABSCENCE OF COMMENT
    class domain0(pg_smallint):
        __pg_check: pg_type_check = pg_type_check[pg_smallint](name='domain_greater_than_0',
                                                               predicate=ge_[pg_smallint](literal_(0)))
        __pg_comment: pg_comment = pg_comment('this is a test comment')

    assert hasattr(domain0, '__pg_definition')
    definition: dict[str, str] = getattr(domain0, '__pg_definition')()
    assert 'type_name' in definition
    assert definition['type_name'] == 'domain0'
    assert 'base_type_name' in definition
    assert definition['base_type_name'] == 'smallint'
    assert 'comment' in definition
    assert definition['comment'] == 'this is a test comment'
    assert 'check' in definition
    assert 'name' in definition['check']
    assert definition['check']['name'] == 'domain_greater_than_0'
    assert 'constraint' in definition['check']
    assert definition['check']['constraint'] == '(VALUE >= 0)'

    # CHECK FOR ABSCENCE OF COMMENT
    class domain1(pg_smallint):
        __pg_check: pg_type_check = pg_type_check[pg_smallint](name='domain_greater_than_0',
                                                               predicate=ge_[pg_smallint](literal_(0)))

    assert hasattr(domain1, '__pg_definition')
    definition: dict[str, str] = getattr(domain1, '__pg_definition')()
    assert 'type_name' in definition
    assert definition['type_name'] == 'domain1'
    assert 'base_type_name' in definition
    assert definition['base_type_name'] == 'smallint'
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert 'name' in definition['check']
    assert definition['check']['name'] == 'domain_greater_than_0'
    assert 'constraint' in definition['check']
    assert definition['check']['constraint'] == '(VALUE >= 0)'

    # CHECK FOR ABSENCE OF COMMENT
    class domain2(pg_smallint):
        __pg_check: pg_type_check = pg_type_check[pg_smallint](name='domain_greater_than_0',
                                                               predicate=ge_[pg_smallint](literal_(0)))

    assert hasattr(domain2, '__pg_definition')
    definition: dict[str, str] = getattr(domain2, '__pg_definition')()
    assert 'type_name' in definition
    assert definition['type_name'] == 'domain2'
    assert 'base_type_name' in definition
    assert definition['base_type_name'] == 'smallint'
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert 'name' in definition['check']
    assert definition['check']['name'] == 'domain_greater_than_0'
    assert 'constraint' in definition['check']
    assert definition['check']['constraint'] == '(VALUE >= 0)'

    # CHECK FOR ABSENCE OF CHECK
    class domain3(pg_smallint):
        __pg_comment: pg_comment = pg_comment('test comment')

    assert hasattr(domain3, '__pg_definition')
    definition: dict[str, str] = getattr(domain3, '__pg_definition')()
    assert 'type_name' in definition
    assert definition['type_name'] == 'domain3'
    assert 'base_type_name' in definition
    assert definition['base_type_name'] == 'smallint'
    assert 'comment' in definition
    assert definition['comment'] == 'test comment'
    assert 'check' in definition
    assert definition['check'] is None

    # CHECK FOR ABSENCE OF COMMENT CHECK AND COMMENT
    class domain4(pg_smallint):
        pass

    assert hasattr(domain4, '__pg_definition')
    definition: dict[str, str] = getattr(domain4, '__pg_definition')()
    assert 'type_name' in definition
    assert definition['type_name'] == 'domain4'
    assert 'base_type_name' in definition
    assert definition['base_type_name'] == 'smallint'
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert definition['check'] is None


def test_builtin_domain_inherits_check_constraint() -> None:
    class domain0(pg_smallint):
        __pg_check: pg_type_check = pg_type_check[pg_smallint](name='domain_greater_than_0',
                                                               predicate=ge_[pg_smallint](literal_(0)))

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
    assert 'type_name' in definition
    assert definition['type_name'] == 'domain1'
    assert 'base_type_name' in definition
    assert definition['base_type_name'] == 'domain0'
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert 'name' in definition['check']
    assert definition['check']['name'] == 'domain_greater_than_0'
    assert 'constraint' in definition['check']
    assert definition['check']['constraint'] == '(VALUE >= 0)'


def test_builtin_domain_merges_inherited_check_constraint() -> None:
    class domain0(pg_smallint):
        __pg_check: pg_type_check = pg_type_check[pg_smallint](name='domain_greater_than_0',
                                                               predicate=ge_[pg_smallint](literal_(0)))

    class domain1(domain0):
        __pg_check: pg_type_check = pg_type_check[pg_smallint](name='domain_less_than_5',
                                                               predicate=le_[pg_smallint](literal_(5)))

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
    assert 'type_name' in definition
    assert definition['type_name'] == 'domain1'
    assert 'base_type_name' in definition
    assert definition['base_type_name'] == 'domain0'
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'check' in definition
    assert 'name' in definition['check']
    assert definition['check']['name'] == 'domain_less_than_5'
    assert 'constraint' in definition['check']
    assert definition['check']['constraint'] == '(VALUE <= 5)'
    assert hasattr(domain1, '_domain0__pg_check')
    assert hasattr(domain1, '_domain1__pg_check')
