from enum import\
    auto
import pgdriver as pg
from typing import\
    Optional


def test_enums_definition_flow_executes_correctly() -> None:
    # NOTE: test that definitions get correctly extracted
    class test0(pg.enums):
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
        class test0(pg.enums):
            FIELD = 1
        assert False
    except TypeError as e:
        assert str(e) == '1 is not a string'

    # NOTE: test that flow detects inheritance from more than one class
    try:
        class test:
            pass

        class test0(pg.enums, test):
            FIELD = 1
        assert False
    except TypeError as e:
        assert str(e) == 'new enumerations should be created as `EnumName([mixin_type, ...] [data_type,] enum_type)`'


def test_enums_domain_definition_flow_executes_correctly() -> None:
    # NOTE: enums definition flow detects domain declaring additional members
    try:
        class test0(pg.enums):
            FIELD = auto()

        class test1(test0):
            FIELD1 = auto()
        assert False
    except pg.FlowException as e:
        error: Optional[pg.NodeException] = e.get_error('enums-definition-flow',
                                                         'enums-domain-validate-members-node')
        assert error is not None
        assert str(error) == "<enum 'test1'> enums cant define own member FIELD1 if it inherits from a <enum 'enums'> subclass"

    # NOTE: enums definition flow detects domain declaring additional members
    class test2(pg.enums):
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
        class test5(pg.enums):
            FIELD1 = auto()

        class test6(test5):
            FIELD1 = auto()
    except TypeError as e:
        assert str(e) == "'FIELD1' already defined as 'field1'"


def test_comments_correctly_added_to_enums_definition() -> None:
    @pg.comment('test comment')
    class test0(pg.enums):
        FIELD = auto()

    assert hasattr(test0, '__pg_definition')
    def0 = getattr(test0, '__pg_definition')()
    assert 'comment' in def0
    assert def0['comment'] == pg.meta.comment('test comment')

    class test1(test0):
        pass

    assert hasattr(test1, '__pg_definition')
    def1 = getattr(test1, '__pg_definition')()
    assert 'comment' in def1
    assert def1['comment'] is None

    @pg.comment('test comment')
    class test2(test1):
        pass

    assert hasattr(test2, '__pg_definition')
    def2 = getattr(test2, '__pg_definition')()
    assert 'comment' in def2
    assert def2['comment'] == pg.meta.comment('test comment')


def test_default_value_to_enums_definition() -> None:
    try:
        @pg.default_value('test comment')
        class test0(pg.enums):
            FIELD1 = auto()
        assert False
    except KeyError as e:
        assert str(e) == "'default_value'"

    class test1(pg.enums):
        FIELD1 = auto()

    @pg.default_value('field1')
    class test2(test1):
        pass

    assert hasattr(test2, '__pg_definition')
    def2 = getattr(test2, '__pg_definition')()
    assert 'default_value' in def2
    assert isinstance(def2['default_value'], pg.meta.default_value)
    assert def2['default_value'].default._lit == test2('field1')

    try:
        class test3(pg.enums):
            FIELD1 = auto()

        @pg.default_value('test')
        class test4(test3):
            pass
        assert False
    except ValueError as e:
        assert str(e) == "'test' is not a valid test_default_value_to_enums_definition.<locals>.test4"

