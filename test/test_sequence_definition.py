from pgdriver.definition.build import\
    pg_sequence,\
    pg_default_sequence_nextval,\
    pg_bigint_sequence,\
    pg_int_sequence,\
    pg_smallint_sequence,\
    pg_smallint,\
    pg_int,\
    pg_table,\
    pg_comment
from pgdriver.definition.build import\
    with_pg_comment,\
    with_pg_min_value,\
    with_pg_max_value,\
    with_pg_increment
from typing_extensions import\
    Annotated
import pydantic_core


def test_sequence_definition_flow_correctly_executed() -> None:
    # NOTE doesnt allow multiple base classes
    try:
        class test0(pg_sequence):
            pass
        class test1(pg_int_sequence, test0):
            pass
    except TypeError as e:
        assert str(e) == 'Class doesnt allow multiple bases'

    # NOTE must inherit from pg_smallint_sequence, pg_int_sequence or pg_bigint_sequence,
    try:
        class test2(pg_int_sequence):
            pass
        class test3(test2):
            pass
    except TypeError as e:
        assert str(e) == "Class test3 must be a subclass of any of these classes (<class 'pgdriver.definition.base.sequence.pg_bigint_sequence'>, <class 'pgdriver.definition.base.sequence.pg_int_sequence'>, <class 'pgdriver.definition.base.sequence.pg_smallint_sequence'>)"

    # NOTE test that definition is correctly extracted
    class test4(pg_smallint_sequence):
        pass

    assert hasattr(test4, '__pg_definition')
    def4 = getattr(test4, '__pg_definition')()
    assert 'base_type' in def4
    assert def4['base_type'] == pg_smallint
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
    @with_pg_comment('test comment')
    @with_pg_min_value(0)
    @with_pg_max_value(10)
    @with_pg_increment(5)
    class test0(pg_int_sequence):
        pass

    assert hasattr(test0, '__pg_definition')
    def0 = getattr(test0, '__pg_definition')()
    assert 'base_type' in def0
    assert def0['base_type'] == pg_int
    assert 'comment' in def0
    assert def0['comment'] == pg_comment('test comment')
    assert def0['min_value'] == 0
    assert def0['max_value'] == 10
    assert def0['increment'] == 5


def test_sequence_schema_correctly_applied_when_used_in_table_description() -> None:
    # NOTE restrictions added by decorators are correctly applied when used in a table
    @with_pg_min_value(0)
    @with_pg_max_value(10)
    class test_seq(pg_int_sequence):
        pass

    class test(pg_table):
        id: Annotated[pg_int, pg_default_sequence_nextval(seq=test_seq)]

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
        class test(pg_table):
            id: Annotated[pg_smallint, pg_default_sequence_nextval(seq=test_seq)]
    except TypeError as e:
        assert str(e) == 'Sequence type must match annotated type'
