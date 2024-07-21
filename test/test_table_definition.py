from pgdriver.definition.types.metadata import \
    pg_unique,\
    pg_index,\
    pg_check
from pgdriver.definition.types.check import\
    LiteralRef,\
    FieldRef,\
    AttributeRef,\
    attr_,\
    ge_,\
    le_,\
    gt_,\
    and_,\
    add_,\
    sub_,\
    Length
from decimal import\
    Decimal
from pgdriver.definition.types.table import\
    pg_table
from pgdriver.definition.types.metadata import\
    pg_foreign_key
from pgdriver.definition.types.builtin import\
    pg_int,\
    pg_text,\
    pg_decimal
from typing_extensions import \
    Annotated
from pgdriver.definition import \
    pgdriver_definition_flow_registry
from pgdriver.definition.flow import\
    FlowAccumulator,\
    FlowEndException


class test(pg_table):
    test_field1: Annotated[pg_int,
                           pg_index(name='index_1', type='hash'),
                           pg_check[pg_int](
                               predicate=gt_[pg_int](LiteralRef[pg_int](Decimal(14))),
                               name='check_1')]

    test_field2: Annotated[pg_text,
                           pg_index(name='index_1', type='hash'),
                           pg_check[pg_text](
                               predicate=attr_[pg_text, pg_int](Length(), ge_[pg_int](LiteralRef[pg_int](10))),
                               name='check_2'),
                           pg_unique(name='tests')]

    test_field3: Annotated[pg_int,
                           pg_index(name='index_2'),
                           pg_check[pg_int](
                               predicate=and_[pg_int](
                                   ge_[pg_int](LiteralRef[pg_int](0)),
                                   le_[pg_int](
                                       sub_[pg_int](
                                           add_[pg_int](
                                               LiteralRef[pg_int](15),
                                               AttributeRef[pg_int, pg_text](Length(), FieldRef[pg_text]('test_field2'))),
                                           LiteralRef[pg_int](10)))),
                               name='check1')]

    test_field4: Annotated[pg_text,
                           pg_check[pg_text](
                               predicate=attr_[pg_text, pg_int](Length(), gt_[pg_int](AttributeRef[pg_int, pg_text](Length(), FieldRef[pg_text]('test_field2')))),
                               name='check_3'),
                           pg_index(name='index_2')]


class test1(test):
    test_field1: Annotated[pg_int,
                           pg_check[pg_int](
                               predicate=gt_[pg_int](LiteralRef[pg_int](Decimal(14))),
                               name='check_1'),
                           pg_index(name='index_1', type='hash')]

    test1_field2: Annotated[pg_text,
                            pg_index(name='peo', type='hash'),
                            pg_check[pg_text](
                                predicate=attr_[pg_text, pg_int](Length(), ge_[pg_int](LiteralRef[pg_int](10))),
                                name='check2'),
                            pg_unique(name='tests')]

    test1_field3: Annotated[pg_int,
                            pg_index(name='culo'),
                            pg_check[pg_int](
                                predicate=and_[pg_int](
                                    ge_[pg_int](LiteralRef[pg_int](0)),
                                    le_[pg_int](
                                        sub_[pg_int](
                                            add_[pg_int](
                                                LiteralRef[pg_int](15),
                                                AttributeRef[pg_int, pg_text](Length(), FieldRef[pg_text]('culo'))),
                                            LiteralRef[pg_int](10)))),
                                    name='check1')]

    test1_field4:  Annotated[pg_text,
                             pg_check[pg_text](
                                predicate=attr_[pg_text, pg_int](Length(), gt_[pg_int](AttributeRef[pg_int, pg_text](Length(), FieldRef[pg_text]('culo')))),
                                name='check3'),
                             pg_index(name='culo')]


class test2(pg_table):
    test2_field1: Annotated[pg_int,
                            pg_foreign_key(
                                other_class=test1,
                                other_class_column_name='field1',
                                name='test2'),
                            pg_unique(name='test2_unique')]

    test2_field2: Annotated[pg_text,
                            pg_index(name='peo', type='hash'),
                            pg_foreign_key(
                                other_class=test1,
                                other_class_column_name='field2',
                                name='test2'),
                            pg_unique(name='test2_unique')]


def test_obtain_definition():
    # accumulator: FlowAccumulator = pgdriver_definition_flow_registry.execute_definition_flow(test2)
    # print(str(accumulator))
    print(pg_int(2))
    assert False

# 
# def test_valid_base_classes():
#     """
#     - Test that the flow detects base classes correctly
#     """
#     assert False
# 
# 
# def test_invalid_base_classes():
#     """
#     - Test that the flow detects when one of the base classes is not a pg_table subclass
#     - Test that the flow detects when at least one of the base class attributes is redefined
#     in the new class.
#     """
#     assert False
# 
# 
# def test_correct_unique_indexes_classes():
#     """
#     - Test that the flow 
#     """
#     accumulator: FlowAccumulator = pgdriver_definition_flow_registry.execute_definition_flow(test2)
#     print(str(accumulator))
#     assert False



