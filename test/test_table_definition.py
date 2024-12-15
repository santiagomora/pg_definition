import pgdriver as pg
from typing_extensions import\
    Annotated
from typing import\
    Optional,\
    Any
from dataclasses import\
    dataclass
from pgdriver.definition.common.inspection import\
    extract_first_instance_from_field_metadata


def test_table_definition_is_correctly_formed() -> None:

    class test(pg.table):
        field_1: pg.int2
        field_2: pg.text

    assert hasattr(test, '__pg_definition')
    definition: dict[str, Any] = test.__pg_definition()
    assert 'type' in definition
    assert definition['type'] == test
    assert 'base_classes' in definition
    assert definition['base_classes'] is None
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'columns' in definition
    assert any([col['name'] == 'field_1' for col in definition['columns'].values()])
    assert any([col['name'] == 'field_2' for col in definition['columns'].values()])
    assert all([col['comment'] is None for col in definition['columns'].values()])
    assert any([col['type'] == pg.text for col in definition['columns'].values()])
    assert any([col['type'] == pg.int2 for col in definition['columns'].values()])
    assert 'primary_key' in definition
    assert definition['primary_key'] is None
    assert 'foreign_keys' in definition
    assert definition['foreign_keys'] == {}
    assert 'indexes' in definition
    assert definition['indexes'] == {}

    @pg.comment('test meta.comment')
    class test2(pg.table):
        field_1: pg.int2
        field_2: Annotated[pg.text, pg.meta.comment('field 2 test meta.comment')]

    assert hasattr(test, '__pg_definition')
    definition: dict[str, Any] = test2.__pg_definition()
    assert 'type' in definition
    assert definition['type'] == test2
    assert 'base_classes' in definition
    assert definition['base_classes'] is None
    assert 'comment' in definition
    assert definition['comment'].value == 'test meta.comment'
    assert 'columns' in definition
    assert any([col['name'] == 'field_1' for col in definition['columns'].values()])
    assert any([col['name'] == 'field_2' for col in definition['columns'].values()])
    assert any([col['type'] == pg.text for col in definition['columns'].values()])
    assert any([col['type'] == pg.int2 for col in definition['columns'].values()])
    assert any([col['comment'] == pg.meta.comment('field 2 test meta.comment') for col in definition['columns'].values()])
    assert 'primary_key' in definition
    assert definition['primary_key']  is None
    assert 'foreign_keys' in definition
    assert definition['foreign_keys'] == {}
    assert 'indexes' in definition
    assert definition['indexes'] == {}


def test_definition_flow_detects_inconsistent_base_classes_and_fields() -> None:
    try:
        class test1(pg.table):
            field_1: pg.int2
            field_2: pg.text

        class test2(pg.table, test1):
            pass
    except TypeError as e:
        assert str(e) == 'Cannot create a consistent method resolution\n\
order (MRO) for bases table, test1'

    try:
        class test1:
            pass

        class test2(pg.table, test1):
            field_1: pg.int2
            field_2: pg.text
    except pg.FlowException as e:
        error: Optional[pg.NodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-consistent-base-classes-node')
        assert error is not None
        assert str(error) == f'Cant define {pg.table} as base class if <class \'test_table_definition.test_definition_flow_detects_inconsistent_base_classes_and_fields.<locals>.test2\'> is set to inherit more than one base class, Inherited class <class \'test_table_definition.test_definition_flow_detects_inconsistent_base_classes_and_fields.<locals>.test1\'> must be a subclass of {pg.table}'

    try:
        class test1(pg.table):
            field_1: pg.int2

        class test2(test1):
            field_1: pg.text

    except pg.FlowException as e:
        error: Optional[pg.NodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-consistent-base-classes-node')
        assert error is not None
        assert str(error) == f'Field field_1 type conflict. Declared in multiple base classes: {pg.int2}, {pg.text}' or \
            str(error) == f'Field field_1 type conflict. Declared in multiple base classes: {pg.text}, {pg.int2}'


def test_definition_flow_detects_empty_table_definition() -> None:
    try:
        class test1(pg.table):
            pass

    except pg.FlowException as e:
        error: Optional[pg.NodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-existing-columns-node')
        assert error is not None
        assert str(error) == "Class <class 'test_table_definition.test_definition_flow_detects_empty_table_definition.<locals>.test1'> must define columns."


# index,\
# unique_constraint,\
# primary_key,\
# foreign_key,\
# pg.meta.default_nextval
def test_definition_flow_detects_repeated_metadata_instances() -> None:
    try:
        class test1(pg.table):
            field: Annotated[pg.int4, pg.meta.default_value(1), pg.meta.default_value(2)]
        assert False
    except pg.FlowException as e:
        error: Optional[pg.NodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-unique-metadata-types-node')
        assert error is not None
        assert str(error) == f'Metadata type {pg.meta.default_value} can only appear once in field declaration'

    try:
        class test_seq(pg.int2_sequence):
            pass

        class test1(pg.table):
            field: Annotated[pg.int4, pg.meta.default_nextval(seq=test_seq)]
        assert False
    except TypeError as e:
        assert str(e) == 'Sequence type must match annotated type'

    try:
        class test_seq(pg.int2_sequence):
            pass

        class test1(pg.table):
            field: Annotated[pg.int2, pg.meta.default_nextval(seq=test_seq), pg.meta.default_nextval(seq=test_seq)]
        assert False
    except pg.FlowException as e:
        error: Optional[pg.NodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-unique-metadata-types-node')
        assert error is not None
        assert str(error) == f'Metadata type {pg.meta.default_nextval} can only appear once in field declaration'

    try:
        class test1(pg.table):
            field: Annotated[pg.int2, pg.meta.comment('test'), pg.meta.comment('tes2')]
        assert False
    except pg.FlowException as e:
        error: Optional[pg.NodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-unique-metadata-types-node')
        assert error is not None
        assert str(error) == f'Metadata type {pg.meta.comment} can only appear once in field declaration'


def test_definition_flow_detects_mutually_exclusive_metadata_types() -> None:
    try:
        class test_seq(pg.int2_sequence):
            pass

        class test(pg.table):
            field1: Annotated[pg.int2,
                              pg.meta.default_value(2),
                              pg.meta.default_nextval(seq=test_seq)]

        assert False
    except pg.FlowException as e:
        error: Optional[pg.NodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-mutually-exclusive-metadata-node')
        assert error is not None
        assert str(error) == f'Field field1 described by two mutually exclusive metadata instances: {pg.meta.default_nextval(seq=test_seq)} and meta.default_value(2)'


def test_definition_flow_detects_invalid_metadata_types() -> None:
    try:
        @pg.primary_key(name='test', columns=('field1', ))
        class test2(pg.table):
            field1: pg.int2

        class test_seq(pg.int2_sequence):
            pass

        @pg.primary_key(name='test_pk', columns=('field1', ))
        @pg.index(name='test_ix', columns=('field1', ))
        @pg.unique_constraint(name='test_ucnt', columns=('field1', ))
        @pg.foreign_key(name='test_fk', other_class=test2,
                        columns=('field1', ), other_class_columns=('field1', ))
        class test1(pg.table):
            field1: Annotated[pg.int2,
                              pg.meta.check(name='test', predicate=pg.this()>pg.literal(0)),
                              pg.meta.default_nextval(seq=test_seq),
                              pg.meta.comment('TEST')]
    except Exception as e:
        print(str(e))
        assert False

    try:
        @dataclass
        class test2:
            field1: str

        class test1(pg.table):
            field1: Annotated[pg.int2,
                              test2('test')]
        assert False
    except pg.FlowException as e:
        error: Optional[pg.NodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-restricted-metadata-types-node')
        assert error is not None
        assert str(error) == "Invalid metadata type <class 'test_table_definition.test_definition_flow_detects_invalid_metadata_types.<locals>.test2'> in field1 declaration"


def test_foreign_key_definition_correctly_extracted() -> None:
    # NOTE test that referenced columns types are correctly validated
    try:
        @pg.primary_key(name='test2', columns=('field1',))
        class test2(pg.table):
            field1: pg.int4

        @pg.foreign_key(name='test2', other_class=test2, columns=('field',),
                        other_class_columns=('field1', ))
        class test1(pg.table):
            field: pg.int2
    except TypeError as e:
        assert str(e) == "Foreign key column \"field\" type must match with \"field1\" in <class 'test_table_definition.test_foreign_key_definition_correctly_extracted.<locals>.test2'> definition"

    try:
        @pg.primary_key(name='test', columns=('field3', ))
        class test2(pg.table):
            field3: pg.int4

        @pg.foreign_key(name='test2', other_class=test2, columns=('field', ),
                        other_class_columns=('field1', ))
        class test1(pg.table):
            field: pg.int2
    except TypeError as e:
        assert str(e) == "Foreign key column \"field1\" must exist in <class 'test_table_definition.test_foreign_key_definition_correctly_extracted.<locals>.test2'> definition"

    # NOTE test that foreign keys are not inherited
    @pg.primary_key(name='test', columns=('field1', ))
    class test1(pg.table):
        field1: pg.int2

    @pg.foreign_key(name='test2', other_class=test1, columns=('field', ),
                    other_class_columns=('field1', ))
    class test2(pg.table):
        field: pg.int2

    class test3(test2):
        pass

    def2 = test2.__pg_definition()
    def3 = test3.__pg_definition()

    assert def2['foreign_keys'] is not None
    assert len(def2['foreign_keys']) == 1

    assert def2['foreign_keys']['test2']['other_class'] == test1
    assert def2['foreign_keys']['test2']['on_update'] == pg.foreign_key_action.NO_ACTION
    assert def2['foreign_keys']['test2']['on_delete'] == pg.foreign_key_action.NO_ACTION
    assert def2['foreign_keys']['test2']['name'] == 'test2'

    assert def3['foreign_keys'] == {}

    # NOTE test that final definition contains expected data
    # NOTE test that foreign keys are correctly grouped by name in final definition
    @pg.primary_key(name='test', columns=('t4_field1', 't4_field2'))
    class test4(pg.table):
        t4_field1: pg.int2
        t4_field2: pg.text

    @pg.foreign_key(name='test2', other_class=test4, columns=('t5_field1', 't5_field2'),
                    other_class_columns=('t4_field1', 't4_field2'))
    class test5(pg.table):
        t5_field1: pg.int2
        t5_field2: pg.text

    def5 = test5.__pg_definition()
    assert def5['foreign_keys']['test2']['other_class'] == test4
    assert def5['foreign_keys']['test2']['on_update'] == pg.foreign_key_action.NO_ACTION
    assert def5['foreign_keys']['test2']['on_delete'] == pg.foreign_key_action.NO_ACTION
    assert def5['foreign_keys']['test2']['name'] == 'test2'

    # NOTE test that validates that all fields pointed by foreign keys participate in unique index or primary key
    try:
        @pg.primary_key(name='test2', columns=('t6_field2',))
        class test6(pg.table):
            t6_field1: pg.int2
            t6_field2: pg.text

        @pg.foreign_key(name='test2', other_class=test6, columns=('t7_field1', 't7_field2'),
                        other_class_columns=('t6_field1', 't6_field2', ))
        class test7(pg.table):
            t7_field1: pg.int2
            t7_field2: pg.text

        assert False
    except TypeError as e:
        assert str(e) == "Foreign key \"test2\" error: Other class \"<class 'test_table_definition.test_foreign_key_definition_correctly_extracted.<locals>.test6'>\" must define any ('unique_constraints', 'primary_key', 'indexes') constraint over referenced columns ('t6_field1', 't6_field2')"

    try:
        class test6(pg.table):
            t6_field1: pg.int2
            t6_field2: pg.text

        @pg.foreign_key(name='test2', other_class=test6, columns=('t7_field1', 't7_field2'),
                        other_class_columns=('t6_field1', 't6_field2', ))
        class test7(pg.table):
            t7_field1: pg.int2
            t7_field2: pg.text
        assert False
    except TypeError as e:
        assert str(e) == "Foreign key \"test2\" error: Other class \"<class 'test_table_definition.test_foreign_key_definition_correctly_extracted.<locals>.test6'>\" must define any ('unique_constraints', 'primary_key', 'indexes') constraint over referenced columns ('t6_field1', 't6_field2')"

    try:
        @pg.primary_key(name='test', columns=('t6_field1',))
        class test6(pg.table):
            t6_field1: pg.int2
            t6_field2: pg.text

        @pg.foreign_key(name='test2', other_class=test6, columns=('t7_field1','t7_field2'),
                        other_class_columns=('t6_field1', 't6_field2'))
        class test7(pg.table):
            t7_field1: pg.int2
            t7_field2: pg.text
        assert False
    except TypeError as e:
        assert str(e) == "Foreign key \"test2\" error: Other class \"<class 'test_table_definition.test_foreign_key_definition_correctly_extracted.<locals>.test6'>\" must define any ('unique_constraints', 'primary_key', 'indexes') constraint over referenced columns ('t6_field1', 't6_field2')"


def test_primary_key_definition_correctly_extracted() -> None:
    # NOTE test that there can only be one primary key in the definition
    try:
        @pg.primary_key(name='test1', columns=('t1_field1',))
        @pg.primary_key(name='test', columns=('t1_field2',))
        class test1(pg.table):
            t1_field1: pg.int2
            t1_field2: pg.int2
        assert False
    except AssertionError:
        pass

    # NOTE test that primary keys are not inherited
    @pg.primary_key(name='test', columns=('t1_field1', 't1_field2', ))
    class test1(pg.table):
        t1_field1: pg.int2
        t1_field2: pg.int2

    class test2(test1):
        pass

    assert hasattr(test2, '__pg_definition')
    def2 = getattr(test2, '__pg_definition')()
    assert 'primary_key' in def2
    assert def2['primary_key'] is None

    # NOTE test primary key is correctly grouped by name in final definition
    # NOTE test that primary key final definition is correct
    assert hasattr(test1, '__pg_definition')
    def1 = getattr(test1, '__pg_definition')()
    assert 'primary_key' in def1
    assert def1['primary_key']['name'] == 'test'
    assert def1['primary_key']['columns'] == ('t1_field1', 't1_field2')


def test_index_definition_correctly_extracted() -> None:
    # NOTE test index is correctly grouped by name in final definition
    @pg.index(name='test', columns=('t1_field1', 't1_field2', ))
    class test1(pg.table):
        t1_field1: pg.int2
        t1_field2: pg.int2

    assert hasattr(test1, '__pg_definition')
    def1 = getattr(test1, '__pg_definition')()
    assert 'indexes' in def1
    assert len(def1['indexes']) == 1
    assert def1['indexes']['test']['columns'] == ('t1_field1', 't1_field2')
    assert def1['indexes']['test']['type'] == pg.index_type.BTREE
    assert def1['indexes']['test']['name'] == 'test'

    # NOTE test that columns can appear in several indexes
    @pg.index(name='test', columns=('t2_field1', 't2_field2', ))
    @pg.index(name='test1', columns=('t2_field1', 't2_field3', ))
    class test2(pg.table):
        t2_field1: pg.int2
        t2_field2: pg.int2
        t2_field3: pg.int2

    assert hasattr(test2, '__pg_definition')
    def2 = getattr(test2, '__pg_definition')()
    assert 'indexes' in def2
    assert len(def2['indexes']) == 2
    print(def2['indexes'])
    assert any([ix['columns'] == ('t2_field1', 't2_field2') for ix in def2['indexes'].values()])
    assert any([ix['columns'] == ('t2_field1', 't2_field3') for ix in def2['indexes'].values()])
    assert any([ix['name'] == 'test' for ix in def2['indexes'].values()])
    assert any([ix['name'] == 'test1' for ix in def2['indexes'].values()])
    assert all([ix['type'] == pg.index_type.BTREE for ix in def2['indexes'].values()])

    # NOTE test that indexes are not inherited
    class test3(test2):
        pass

    assert hasattr(test3, '__pg_definition')
    def3 = getattr(test3, '__pg_definition')()
    assert 'indexes' in def3
    assert def3['indexes'] == {}

    try:
        @pg.index(name='test1', columns=('t2_field1', ))
        @pg.index(name='test1', columns=('t2_field1', ))
        class test4(pg.table):
            t2_field1: pg.int2
    except AssertionError:
        pass


def test_unique_constraint_definition_correctly_extracted() -> None:
    # NOTE test unique index is correctly grouped by name in final definition
    @pg.unique_constraint(name='test', columns=('t1_field1', 't1_field2', ))
    class test1(pg.table):
        t1_field1: pg.int2
        t1_field2: pg.int2

    assert hasattr(test1, '__pg_definition')
    def1 = getattr(test1, '__pg_definition')()
    assert 'unique_constraints' in def1
    assert isinstance(def1['unique_constraints'], dict)
    assert def1['unique_constraints']['test']['columns'] == ('t1_field1', 't1_field2')
    assert def1['unique_constraints']['test']['name'] == 'test'

    # NOTE test that columns can appear in several indexes
    @pg.unique_constraint(name='test', columns=('t2_field1', 't2_field2', ))
    @pg.unique_constraint(name='test1', columns=('t2_field2', 't2_field3', ))
    class test2(pg.table):
        t2_field1: pg.int2
        t2_field2: pg.int2
        t2_field3: pg.int2
    assert hasattr(test2, '__pg_definition')
    def2 = getattr(test2, '__pg_definition')()
    assert 'unique_constraints' in def2
    assert len(def2['unique_constraints']) == 2
    assert any([ix['columns'] == ('t2_field1', 't2_field2') for _, ix in def2['unique_constraints'].items()])
    assert any([ix['columns'] == ('t2_field2', 't2_field3') for _, ix in def2['unique_constraints'].items()])
    assert any([ix['name'] == 'test' for ix in def2['unique_constraints'].values()])
    assert any([ix['name'] == 'test1' for ix in def2['unique_constraints'].values()])

    # NOTE test that unique indexes are not inherited
    class test3(test2):
        pass
    assert hasattr(test3, '__pg_definition')
    def3 = getattr(test3, '__pg_definition')()
    assert 'unique_constraints' in def3
    assert def3['unique_constraints'] == {}

    try:
        @pg.unique_constraint(name='test', columns=('t2_field1',))
        @pg.unique_constraint(name='test', columns=('t2_field1',))
        class test4(pg.table):
            t2_field1: pg.int2
    except AssertionError:
        pass


def test_check_definition_correctly_extracted() -> None:
    # NOTE test that pg.meta.check constraints are not inherited
    class test0(pg.table):
        t0_field1: Annotated[pg.int2,
                             pg.meta.check(name='test', predicate=pg.this() > pg.literal(0))]
    class test1(pg.table):
        t1_field1: Annotated[pg.int2,
                             pg.meta.check(name='test', predicate=pg.this() < pg.literal(10))]

    class test2(test0, test1):
        pass

    # test0
    assert hasattr(test0, '__pg_definition')
    def0 = getattr(test0, '__pg_definition')()
    assert 'columns' in def0
    assert isinstance(def0['columns'] , dict)
    assert def0['columns']['t0_field1']['name'] == 't0_field1'
    assert def0['columns']['t0_field1']['type'] == pg.int2
    assert def0['columns']['t0_field1']['comment'] is None
    assert 'check' in def0
    assert isinstance(def0['check'], dict)
    assert 'test0_test' in def0['check']
    assert def0['check']['test0_test'].name == 'test0_test'
    assert str(def0['check']['test0_test']) == '(t0_field1 > 0)'
    assert 'base_classes' in def0
    assert def0['base_classes'] is None
    # test1
    assert hasattr(test1, '__pg_definition')
    def1 = getattr(test1, '__pg_definition')()
    assert 'columns' in def1
    assert isinstance(def1['columns'] , dict)
    assert len(def1['columns']) == 1
    assert def1['columns']['t1_field1']['name'] == 't1_field1'
    assert def1['columns']['t1_field1']['type'] == pg.int2
    assert def1['columns']['t1_field1']['comment'] is None
    assert 'check' in def1
    assert isinstance(def1['check'], dict)
    assert 'test1_test' in def1['check']
    assert def1['check']['test1_test'].name == 'test1_test'
    assert str(def1['check']['test1_test']) == '(t1_field1 < 10)'
    assert 'base_classes' in def1
    assert def1['base_classes'] is None
    # test2
    assert hasattr(test2, '__pg_definition')
    def2 = getattr(test2, '__pg_definition')()
    assert 'columns' in def2
    assert def2['columns'] == {}
    assert 'base_classes' in def2
    assert def2['base_classes'] == (test0, test1, )
    # NOTE test that pg.meta.check constraints are applied when instancing class
    # NOTE test that parent pg.meta.check constraints are applied when instancing class
    try:
        test0(t0_field1=-1)
        assert False
    except ValueError as e:
        assert str(e) == '1 validation error for test0\n\
t0_field1\n\
  Value error, test0_test: constraint validation failed for value "-1" [type=value_error, input_value=-1, input_type=int]\n\
    For further information visit https://errors.pydantic.dev/2.8/v/value_error'
    try:
        test1(t1_field1=11)
        assert False
    except ValueError as e:
        assert str(e) == '1 validation error for test1\n\
t1_field1\n\
  Value error, test1_test: constraint validation failed for value "11" [type=value_error, input_value=11, input_type=int]\n\
    For further information visit https://errors.pydantic.dev/2.8/v/value_error'
    try:
        test2(t0_field1=2, t1_field1=11)
        assert False
    except ValueError as e:
        assert str(e) == '1 validation error for test1\n\
t1_field1\n\
  Value error, test1_test: constraint validation failed for value "11" [type=value_error, input_value=11, input_type=int]\n\
    For further information visit https://errors.pydantic.dev/2.8/v/value_error'
    try:
        test2(t0_field1=-1, t1_field1=9)
        assert False
    except ValueError as e:
        assert str(e) == '1 validation error for test0\n\
t0_field1\n\
  Value error, test0_test: constraint validation failed for value "-1" [type=value_error, input_value=-1, input_type=int]\n\
    For further information visit https://errors.pydantic.dev/2.8/v/value_error'

    class test3(test2):
        pass

    try:
        test3(t0_field1=2, t1_field1=11)
        assert False
    except ValueError as e:
        assert str(e) == '1 validation error for test1\n\
t1_field1\n\
  Value error, test1_test: constraint validation failed for value "11" [type=value_error, input_value=11, input_type=int]\n\
    For further information visit https://errors.pydantic.dev/2.8/v/value_error'
    try:
        test3(t0_field1=-1, t1_field1=9)
        assert False
    except ValueError as e:
        assert str(e) == '1 validation error for test0\n\
t0_field1\n\
  Value error, test0_test: constraint validation failed for value "-1" [type=value_error, input_value=-1, input_type=int]\n\
    For further information visit https://errors.pydantic.dev/2.8/v/value_error'

    class test4(pg.table):
        t4_field1: Annotated[pg.int2,
                             pg.meta.check(name='test', predicate=pg.this() > pg.literal(0))]
    class test5(pg.table):
        t4_field1: Annotated[pg.int2,
                             pg.meta.check(name='test', predicate=pg.this() < pg.literal(10))]

    class test6(test4, test5):
        pass

    class test7(test6):
        t4_field1: Annotated[pg.int2,
                             pg.meta.check(name='test', predicate=pg.this() > pg.literal(5))]
    try:
        test6(t4_field1=11)
        assert False
    except ValueError as e:
        assert str(e) == '1 validation error for test5\n\
t4_field1\n\
  Value error, test5_test: constraint validation failed for value "11" [type=value_error, input_value=11, input_type=int]\n\
    For further information visit https://errors.pydantic.dev/2.8/v/value_error'
    try:
        test6(t4_field1=-1)
        assert False
    except ValueError as e:
        assert str(e) == '1 validation error for test4\n\
t4_field1\n\
  Value error, test4_test: constraint validation failed for value "-1" [type=value_error, input_value=-1, input_type=int]\n\
    For further information visit https://errors.pydantic.dev/2.8/v/value_error'

    try:
        test7(t4_field1=11)
        assert False
    except ValueError as e:
        assert str(e) == '1 validation error for test5\n\
t4_field1\n\
  Value error, test5_test: constraint validation failed for value "11" [type=value_error, input_value=11, input_type=int]\n\
    For further information visit https://errors.pydantic.dev/2.8/v/value_error'
    try:
        test7(t4_field1=3)
        assert False
    except ValueError as e:
        assert str(e) == '1 validation error for test7\n\
t4_field1\n\
  Value error, test7_test: constraint validation failed for value "3" [type=value_error, input_value=3, input_type=int]\n\
    For further information visit https://errors.pydantic.dev/2.8/v/value_error'

    try:
        class test4(pg.table):
            t2_field1: Annotated[pg.int2,
                                 pg.meta.check(name='test', predicate=pg.this() > pg.literal(0)),
                                 pg.meta.check(name='test', predicate=pg.this() > pg.literal(0))]
    except pg.FlowException as e:
        error: Optional[pg.NodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-same-type-meta-instances-have-different-names-node')
        assert error is not None
        assert str(error) == 'Metadata definition error in t2_field1: found 2 repeated instances of same type check sharing name test.'


def test_default_values_correctly_extracted() -> None:
    # NOTE test that default values are present in final column definition
    class test0(pg.table):
        t0_field1: Annotated[pg.int2,
                             pg.meta.default_value(1)]
    # test0
    assert hasattr(test0, '__pg_definition')
    def0 = getattr(test0, '__pg_definition')()
    assert 'columns' in def0
    assert isinstance(def0['columns'], dict)
    assert 'default_value' in def0['columns']['t0_field1']
    assert isinstance(def0['columns']['t0_field1']['default_value'], pg.meta.default_value)
    assert str(def0['columns']['t0_field1']['default_value'].default) == '1'

    class test_seq(pg.int2_sequence):
        pass

    class test1(pg.table):
        t0_field1: Annotated[pg.int2,
                             pg.meta.default_nextval(seq=test_seq)]


    assert hasattr(test1, '__pg_definition')
    def1 = getattr(test1, '__pg_definition')()
    assert 'columns' in def1
    assert isinstance(def1['columns'], dict)
    assert 'default_value' in def1['columns']['t0_field1']
    assert isinstance(def1['columns']['t0_field1']['default_value'], pg.meta.default_nextval)


def test_comments_correctly_extracted() -> None:
    # NOTE test that pg.meta.comment are present in final definition
    # NOTE test that pg.meta.comments are not inherited from parent classes
    @pg.comment('table test meta.comment')
    class test0(pg.table):
        t0_field1: Annotated[pg.int2,
                             pg.meta.comment('test meta.comment')]
    # test0
    assert hasattr(test0, '__pg_definition')
    def0 = getattr(test0, '__pg_definition')()
    assert 'columns' in def0
    assert isinstance(def0['columns'], dict)
    assert 'comment' in def0['columns']['t0_field1']
    assert isinstance(def0['columns']['t0_field1']['comment'], pg.meta.comment)
    assert def0['columns']['t0_field1']['comment'].value == 'test meta.comment'
    assert 'default_value' in def0['columns']['t0_field1']
    assert def0['columns']['t0_field1']['default_value'] is None
    assert 'comment' in def0
    assert isinstance(def0['comment'], pg.meta.comment)
    assert def0['comment'].value == 'table test meta.comment'
