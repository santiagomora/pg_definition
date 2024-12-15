import pgdriver as pg
from typing_extensions import\
    Annotated
import pydantic_core


def test_sequence_definition_flow_correctly_executed() -> None:
    # NOTE doesnt allow multiple base classes
    try:
        class test0(pg.sequence):
            pass
        class test1(pg.int4_sequence, test0):
            pass
    except TypeError as e:
        assert str(e) == f'Class {pg.sequence} doesnt allow multiple bases'

    # NOTE must inherit from pg.int2_sequence, pg.int4_sequence or pg.int8_sequence,
    try:
        class test2(pg.int4_sequence):
            pass
        class test3(test2):
            pass
    except TypeError as e:
        assert str(e) == f'Class test3 must be a subclass of any of these classes ({pg.int8_sequence}, {pg.int4_sequence}, {pg.int2_sequence})'

    # NOTE test that definition is correctly extracted
    class test4(pg.int2_sequence):
        pass

    assert hasattr(test4, '__pg_definition')
    def4 = getattr(test4, '__pg_definition')()
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
    @pg.comment('test comment')
    @pg.min_value(0)
    @pg.max_value(10)
    @pg.increment(5)
    class test0(pg.int4_sequence):
        pass

    assert hasattr(test0, '__pg_definition')
    def0 = getattr(test0, '__pg_definition')()
    assert 'base_type' in def0
    assert def0['base_type'] == pg.int4
    assert 'comment' in def0
    assert def0['comment'] == pg.meta.comment('test comment')
    assert def0['min_value'] == 0
    assert def0['max_value'] == 10
    assert def0['increment'] == 5


def test_sequence_schema_correctly_applied_when_used_in_table_description() -> None:
    # NOTE restrictions added by decorators are correctly applied when used in a pg.table
    @pg.min_value(0)
    @pg.max_value(10)
    class test_seq(pg.int4_sequence):
        pass

    class test(pg.table):
        id: Annotated[pg.int4, pg.meta.default_nextval(seq=test_seq)]

    try:
        test(id=-1)
        assert False
    except pydantic_core._pydantic_core.ValidationError as e:
        assert str(e) == "1 validation error for test\n\
id\n\
  Value error, Value cant be less than sequence min value [type=value_error, input_value=-1, input_type=int]\n\
    For further information visit https://errors.pydantic.dev/2.8/v/value_error"
    try:
        test(id=11)
        assert False
    except pydantic_core._pydantic_core.ValidationError as e:
        assert str(e) == "1 validation error for test\n\
id\n\
  Value error, Value cant be greater than sequence max value [type=value_error, input_value=11, input_type=int]\n\
    For further information visit https://errors.pydantic.dev/2.8/v/value_error"

    try:
        class test(pg.table):
            id: Annotated[pg.int2, pg.meta.default_nextval(seq=test_seq)]
    except TypeError as e:
        assert str(e) == 'Sequence type must match annotated type'
