from enum import\
    auto
import pg_definition as pg
from typing import\
    Optional
import test_app.backend.types as tat
import test_app.backend.cpp.wrapper as tw


def test_enums_definition_flow_executes_correctly() -> None:
    # NOTE: test that definitions get correctly extracted
    class test0(tw.post_status, metaclass=pg.enum):
        pass

    assert hasattr(test0, '__pg_definition')
    def0 = getattr(test0, '__pg_definition')()
    assert 'type' in def0
    assert def0['type'] == test0
    assert 'comment' in def0
    assert def0['comment'] is None
    assert 'members' in def0
    assert isinstance(def0['members'], dict)
    for memb in def0['members']:
        assert test0.__members__[memb.name].value == def0['members'][memb]

    # NOTE: test that members are string
    # try:
    #     class test0(pg.enums):
    #         FIELD = 1
    #     assert False
    # except TypeError as e:
    #     assert str(e) == '1 is not a string'
    # 
    # NOTE: test that flow detects inheritance from more than one class
    # try:
    #     class test:
    #         pass
    # 
    #     class test0(pg.enum, test):
    #         FIELD = 1
    #     assert False
    # except TypeError as e:
    #     assert str(e) == 'new enumerations should be created as `EnumName([mixin_type, ...] [data_type,] enum_type)`'


def test_enums_domain_definition_flow_executes_correctly() -> None:
    # NOTE: enums definition flow detects domain declaring additional members
    class test0(tw.post_status, metaclass=pg.enum):
        pass

    class test1(test0, default=pg.literal(test0.published)):
        FIELD1 = 1

    assert hasattr(test1, '__pg_definition')
    def1 = getattr(test1, '__pg_definition')()
    assert 'type' in def1
    assert def1['type'] == test1
    assert 'base_type' in def1
    assert def1['base_type'] == test0
    assert 'comment' in def1
    assert def1['comment'] is None
    assert 'default' in def1
    assert isinstance(def1['default'], pg.literal)
    assert def1['default']._lit == test0.published


def test_comments_correctly_added_to_enums_definition() -> None:
    @pg.add_comment('test comment')
    class test0(tw.post_status, metaclass=pg.enum):
        pass

    assert hasattr(test0, '__pg_definition')
    def0 = getattr(test0, '__pg_definition')()
    assert 'comment' in def0
    assert def0['comment'] == pg.comment('test comment')

    class test1(test0):
        pass

    assert hasattr(test1, '__pg_definition')
    def1 = getattr(test1, '__pg_definition')()
    assert 'comment' in def1
    assert def1['comment'] is None

    @pg.add_comment('test comment')
    class test2(test1):
        pass

    assert hasattr(test2, '__pg_definition')
    def2 = getattr(test2, '__pg_definition')()
    assert 'comment' in def2
    assert def2['comment'] == pg.comment('test comment')


# def test_default_value_to_enums_definition() -> None:
#     try:
#         @pg.default_value('test comment')
#         class test0(pg.enums):
#             FIELD1 = auto()
#         assert False
#     except KeyError as e:
#         assert str(e) == "'default'"
# 
#     class test1(pg.enums):
#         FIELD1 = auto()
# 
#     @pg.default_value('field1')
#     class test2(test1):
#         pass
# 
#     assert hasattr(test2, '__pg_definition')
#     def2 = getattr(test2, '__pg_definition')()
#     assert 'default' in def2
#     assert isinstance(def2['default'], pg.literal)
#     assert def2['default']._lit == test2('field1')
# 
#     try:
#         class test3(pg.enums):
#             FIELD1 = auto()
# 
#         @pg.default_value('test')
#         class test4(test3):
#             pass
#         assert False
#     except ValueError as e:
#         assert str(e) == "'test' is not a valid test_default_value_to_enums_definition.<locals>.test4"
# 
