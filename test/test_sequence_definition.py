import pg_definition as pg
from typing_extensions import\
    Annotated
import pydantic_core
import test_app.backend.cpp.wrapper as tw


def test_sequence_definition_flow_correctly_executed() -> None:
    # NOTE doesnt allow multiple base classes
    # NOTE must inherit from pg.int2_sequence, pg.int4_sequence or pg.int8_sequence,
    try:
        class test3(pg.sequence, base=int):
            pass
    except TypeError:
        pass

    # NOTE test that definition is correctly extracted
    class test4(pg.sequence, base=pg.int2):
        pass

    assert hasattr(test4, '_postgres_definition')
    def4 = test4._postgres_definition
    assert 'base_type' in def4
    assert def4['base_type'] == pg.int2
    assert 'comment' in def4
    assert def4['comment'] is None
    assert 'min_value' in def4
    assert def4['min_value'] is None
    assert 'max_value' in def4
    assert def4['max_value'] is None
    assert 'increment' in def4
    assert def4['increment'] is None


def test_decorators_correctly_applied() -> None:
    # NOTE decorators are correctly applied
    @pg.sequence.add_comment(value='test comment')
    @pg.sequence.min_value(0)
    @pg.sequence.max_value(10)
    @pg.sequence.increment(5)
    class test0(pg.sequence, base=pg.int4):
        pass

    assert hasattr(test0, '_postgres_definition')
    def0 = test0._postgres_definition
    assert 'base_type' in def0
    assert def0['base_type'] == pg.int4
    assert 'comment' in def0
    assert def0['comment'].value == 'test comment'
    assert def0['min_value'] == 0
    assert def0['max_value'] == 10
    assert def0['increment'] == 5


# def test_sequence_schema_correctly_applied_when_used_in_table_description() -> None:
#     # NOTE restrictions added by decorators are correctly applied when used in a pg.table
#     @pg.min_value(0)
#     @pg.max_value(10)
#     class test_seq(pg.sequence, base=pg.int4):
#         pass
# 
#     try:
#         @pg.serial(column='id', sequence=test_seq)
#         class test(pg.table):
#             id: pg.int2
#     except TypeError as e:
#         assert str(e) == 'Sequence type must match annotated type'
