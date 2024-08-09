from pgdriver.definition.build import \
    pg_meta,\
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
    Length,\
    pg_table,\
    pg_int,\
    pg_text,\
    pg_decimal
from typing import\
    Optional
from decimal import\
    Decimal
from pgdriver.definition.inspection import\
    extract_definition_fields,\
    extract_by_instance_type_from_inherited_classes
from typing_extensions import \
    Annotated
from pgdriver.definition.flows import\
    FlowEndException,\
    FlowComponentException
from pgdriver.definition.registry import\
    valid_pg_definition
import pytest
from annotated_types import\
    Gt

"""
    Suite for testing the following definition validation components
    -
    TableValidateExistingColumnsComponent
    TableValidateConsistentBaseClassesComponent
    TableValidateInheritedFieldsComponent
    TableValidateRestrictedMetadataTypesComponent
    TableValidateUniqueMetadataTypesComponent
    TableValidateFieldsBaseTypeComponent
    TableValidateConsistentForeignKeysComponent
"""


# @pytest.mark.table_definition_flow_validation
def test_flow_rejects_non_registered_target():
    clsname: str = ''
    try:
        class test3:
            pass
        clsname = str(test3)
        valid_pg_definition(test3)
    except Exception as e:
        assert str(e) == f'Context registry: definition flows not defined for {clsname}'


# @pytest.mark.table_definition_flow_validation
def test_flow_detects_undefined_columns():
    clsname: str = ''
    try:
        class test3(pg_table):
            pass
        clsname = str(test3)
        valid_pg_definition(test3)
    except FlowEndException as e:
        error: Optional[FlowComponentException] = e.get_error('pgdriver-table-definition-flow', 'validate-existing-columns-component')
        assert error is not None
        assert f'Class {clsname} must define columns.' in error.error_list


# @pytest.mark.table_definition_flow_validation
def test_table_validation_consistent_base_classes():
    clsname: str = ''
    try:
        class test1:
            pass

        class test2(pg_table):
            pass

        class test3(test1, test2):
            pass

        clsname = str(test1)
        valid_pg_definition(test3)
    except FlowEndException as e:
        error: Optional[FlowComponentException] = e.get_error('pgdriver-table-definition-flow', 'validate-consistent-base-classes-component')
        assert error is not None
        assert f'Inherited class {clsname} must be a subclass of {pg_table}' in error.error_list


def test_table_validation_inherited_fields():
    class test(pg_table):
        field: Annotated[pg_int, pg_meta.index(name='index_1', type='hash')]
        field2: Annotated[pg_int, pg_meta.index(name='index_1', type='hash')]

    @valid_pg_definition
    class testchild(test):
        field: Annotated[pg_int, pg_meta.unique_index(name='index_1')]
        field3: Annotated[pg_int, pg_meta.index(name='index_1', type='hash')]

    assert False


# class test(pg_table):
#     test_field1: Annotated[pg_int,
#                            pg_meta.index(name='index_1', type='hash'),
#                            pg_meta.check[pg_int](
#                                predicate=gt_[pg_int](LiteralRef[pg_int](Decimal(14))),
#                                name='check_1')]
# 
#     test_field2: Annotated[pg_text,
#                            pg_meta.index(name='index_1', type='hash'),
#                            pg_meta.check[pg_text](
#                                predicate=attr_[pg_text, pg_int](Length(), ge_[pg_int](LiteralRef[pg_int](10))),
#                                name='check_2'),
#                            pg_meta.unique_index(name='tests')]
# 
#     test_field3: Annotated[pg_int,
#                            pg_meta.index(name='index_2'),
#                            pg_meta.check[pg_int](
#                                predicate=and_[pg_int](
#                                    ge_[pg_int](LiteralRef[pg_int](0)),
#                                    le_[pg_int](
#                                        sub_[pg_int](
#                                            add_[pg_int](
#                                                LiteralRef[pg_int](15),
#                                                AttributeRef[pg_int, pg_text](Length(), FieldRef[pg_text]('test_field2'))),
#                                            LiteralRef[pg_int](10)))),
#                                name='check1')]
# 
#     test_field4: Annotated[pg_text,
#                            pg_meta.check[pg_text](
#                                predicate=attr_[pg_text, pg_int](Length(), gt_[pg_int](AttributeRef[pg_int, pg_text](Length(), FieldRef[pg_text]('test_field2')))),
#                                name='check_3'),
#                            pg_meta.index(name='index_2')]
# 
# 
# class test1(test):
#     test_field1: Annotated[pg_decimal,
#                            pg_meta.check[pg_int](
#                                predicate=gt_[pg_int](LiteralRef[pg_int](Decimal(14))),
#                                name='check_1'),
#                            pg_meta.index(name='index_1', type='hash')]
# 
#     test1_field2: Annotated[pg_text,
#                             pg_meta.index(name='peo', type='hash'),
#                             pg_meta.check[pg_text](
#                                 predicate=attr_[pg_text, pg_int](Length(), ge_[pg_int](LiteralRef[pg_int](10))),
#                                 name='check2'),
#                             pg_meta.unique_index(name='tests')]
# 
#     test1_field3: Annotated[pg_int,
#                             pg_meta.index(name='culo'),
#                             pg_meta.check[pg_int](
#                                 predicate=and_[pg_int](
#                                     ge_[pg_int](LiteralRef[pg_int](0)),
#                                     le_[pg_int](
#                                         sub_[pg_int](
#                                             add_[pg_int](
#                                                 LiteralRef[pg_int](15),
#                                                 AttributeRef[pg_int, pg_text](Length(), FieldRef[pg_text]('culo'))),
#                                             LiteralRef[pg_int](10)))),
#                                     name='check1')]
# 
#     test1_field4:  Annotated[pg_text,
#                              pg_meta.check[pg_text](
#                                 predicate=attr_[pg_text, pg_int](Length(), gt_[pg_int](AttributeRef[pg_int, pg_text](Length(), FieldRef[pg_text]('culo')))),
#                                 name='check3'),
#                              pg_meta.index(name='culo')]
# 
# 
# @valid_pg_definition
# class test2(pg_table):
#     test2_field1: Annotated[pg_int,
#                             pg_meta.foreign_key(
#                                 other_class=test1,
#                                 other_class_column_name='field1',
#                                 name='test2'),
#                             pg_meta.unique_index(name='test2_unique')]
# 
#     test2_field2: Annotated[pg_text,
#                             pg_meta.index(name='peo', type='hash'),
#                             pg_meta.foreign_key(
#                                 other_class=test1,
#                                 other_class_column_name='field2',
#                                 name='test2'),
#                             pg_meta.unique_index(name='test2_unique')]
