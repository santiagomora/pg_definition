from pgdriver.definition.build import\
    pg_enum
from enum import\
    auto
from typing import\
    Optional
from pgdriver.definition.base.common.flow import\
    FlowEndException,\
    FlowNodeException
from pgdriver.definition.build import\
    with_pg_comment,\
    with_pg_default_value,\
    pg_comment,\
    pg_default_value


def test_enum_definition_flow_executes_correctly() -> None:
    # NOTE: test that definitions get correctly extracted
    class test0(pg_enum):
        FIELD = auto()

    assert hasattr(test0, '__pg_definition')
    def0 = getattr(test0, '__pg_definition')()
    assert 'type' in def0
    assert def0['type'] == test0
    assert 'comment' in def0
    assert def0['comment'] is None
    assert 'members' in def0
    assert isinstance(def0['members'], dict)
    for memb in def0['members']:
        assert test0[memb].value == def0['members'][memb]

    # NOTE: test that members are string
    try:
        class test0(pg_enum):
            FIELD = 1
        assert False
    except TypeError as e:
        assert str(e) == '1 is not a string'

    # NOTE: test that flow detects inheritance from more than one class
    try:
        class test:
            pass

        class test0(pg_enum, test):
            FIELD = 1
        assert False
    except TypeError as e:
        assert str(e) == 'new enumerations should be created as `EnumName([mixin_type, ...] [data_type,] enum_type)`'


def test_enum_domain_definition_flow_executes_correctly() -> None:
    # NOTE: enum definition flow detects domain declaring additional members
    try:
        class test0(pg_enum):
            FIELD = auto()

        class test1(test0):
            FIELD1 = auto()
        assert False
    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('enum-definition-flow',
                                                         'enum-domain-validate-members-node')
        assert error is not None
        assert str(error) == "<enum 'test1'> enum cant define own member FIELD1 if it inherits from a <enum 'pg_enum'> subclass"

    # NOTE: enum definition flow detects domain declaring additional members
    class test2(pg_enum):
        FIELD1 = auto()
        FIELD2 = auto()
        FIELD3 = auto()
        FIELD4 = auto()

    class test3(test2):
        pass

    assert hasattr(test3, '__pg_definition')
    def3 = getattr(test3, '__pg_definition')()
    assert 'type' in def3
    assert def3['type'] == test3
    assert 'base_type' in def3
    assert def3['base_type'] == test2
    assert 'comment' in def3
    assert def3['comment'] is None
    assert 'default_value' in def3
    assert def3['default_value'] is None
    for memb in test3:
        assert memb in test2
        assert test2[memb.name].value == memb.value

    class test4(test3):
        pass

    for memb in test4:
        assert memb in test3
        assert memb in test2
        assert test2[memb.name].value == memb.value
        assert test3[memb.name].value == memb.value

    try:
        class test5(pg_enum):
            FIELD1 = auto()

        class test6(test5):
            FIELD1 = auto()
    except TypeError as e:
        assert str(e) == "'FIELD1' already defined as 'field1'"


def test_comments_correctly_added_to_enum_definition() -> None:
    @with_pg_comment('test comment')
    class test0(pg_enum):
        FIELD = auto()

    assert hasattr(test0, '__pg_definition')
    def0 = getattr(test0, '__pg_definition')()
    assert 'comment' in def0
    assert def0['comment'] == pg_comment('test comment')

    class test1(test0):
        pass

    assert hasattr(test1, '__pg_definition')
    def1 = getattr(test1, '__pg_definition')()
    assert 'comment' in def1
    assert def1['comment'] is None

    @with_pg_comment('test comment')
    class test2(test1):
        pass

    assert hasattr(test2, '__pg_definition')
    def2 = getattr(test2, '__pg_definition')()
    assert 'comment' in def2
    assert def2['comment'] == pg_comment('test comment')


def test_default_value_to_enum_definition() -> None:
    try:
        @with_pg_default_value('test comment')
        class test0(pg_enum):
            FIELD1 = auto()
        assert False
    except KeyError as e:
        assert str(e) == "'default_value'"

    class test1(pg_enum):
        FIELD1 = auto()

    @with_pg_default_value('field1')
    class test2(test1):
        pass

    assert hasattr(test2, '__pg_definition')
    def2 = getattr(test2, '__pg_definition')()
    assert 'default_value' in def2
    assert isinstance(def2['default_value'], pg_default_value)
    assert def2['default_value'].default._lit == test2('field1')

    try:
        class test3(pg_enum):
            FIELD1 = auto()

        @with_pg_default_value('test')
        class test4(test3):
            pass
        assert False
    except ValueError as e:
        assert str(e) == "'test' is not a valid test_default_value_to_enum_definition.<locals>.test4"

