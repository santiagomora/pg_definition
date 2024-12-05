from pgdriver import\
    smallint,\
    text,\
    table,\
    integer,\
    with_comment,\
    comment,\
    check,\
    default_value,\
    table_index,\
    table_unique_index,\
    table_primary_key,\
    table_foreign_key,\
    default_nextval,\
    literal,\
    smallint_sequence,\
    this,\
    FlowEndException,\
    FlowNodeException,\
    table_index_type,\
    table_foreign_key_action
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

    class test(table):
        field_1: smallint
        field_2: text

    assert hasattr(test, '__pg_definition')
    definition: dict[str, Any] = test.__pg_definition()
    assert 'class' in definition
    assert definition['class'] == test
    assert 'base_classes' in definition
    assert definition['base_classes'] is None
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'columns' in definition
    assert any([col['name'] == 'field_1' for col in definition['columns']])
    assert any([col['name'] == 'field_2' for col in definition['columns']])
    assert all([col['comment'] is None for col in definition['columns']])
    assert any([col['type'] == text for col in definition['columns']])
    assert any([col['type'] == smallint for col in definition['columns']])
    assert 'primary_key' in definition
    assert definition['primary_key']  is None
    assert 'foreign_keys' in definition
    assert definition['foreign_keys']  is None
    assert 'indexes' in definition
    assert definition['indexes']  is None

    @with_comment('test comment')
    class test2(table):
        field_1: smallint
        field_2: Annotated[text, comment('field 2 test comment')]

    assert hasattr(test, '__pg_definition')
    definition: dict[str, Any] = test2.__pg_definition()
    assert 'class' in definition
    assert definition['class'] == test2
    assert 'base_classes' in definition
    assert definition['base_classes'] is None
    assert 'comment' in definition
    assert definition['comment'].value == 'test comment'
    assert 'columns' in definition
    assert any([col['name'] == 'field_1' for col in definition['columns']])
    assert any([col['name'] == 'field_2' for col in definition['columns']])
    assert any([col['type'] == text for col in definition['columns']])
    assert any([col['type'] == smallint for col in definition['columns']])
    assert any([col['comment'] == comment('field 2 test comment') for col in definition['columns']])
    assert 'primary_key' in definition
    assert definition['primary_key']  is None
    assert 'foreign_keys' in definition
    assert definition['foreign_keys']  is None
    assert 'indexes' in definition
    assert definition['indexes']  is None


def test_definition_flow_detects_inconsistent_base_classes_and_fields() -> None:
    try:
        class test1(table):
            field_1: smallint
            field_2: text

        class test2(table, test1):
            pass
    except TypeError as e:
        assert str(e) == 'Cannot create a consistent method resolution\n\
order (MRO) for bases table, test1'

    try:
        class test1:
            pass

        class test2(table, test1):
            field_1: smallint
            field_2: text
    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-consistent-base-classes-node')
        assert error is not None
        assert str(error) == f'Cant define {table} as base class if <class \'test_table_definition.test_definition_flow_detects_inconsistent_base_classes_and_fields.<locals>.test2\'> is set to inherit more than one base class, Inherited class <class \'test_table_definition.test_definition_flow_detects_inconsistent_base_classes_and_fields.<locals>.test1\'> must be a subclass of {table}'

    try:
        class test1(table):
            field_1: smallint

        class test2(test1):
            field_1: text

    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-consistent-base-classes-node')
        assert error is not None
        assert str(error) == f'Field field_1 type conflict. Declared in multiple base classes: {smallint}, {text}' or \
            str(error) == f'Field field_1 type conflict. Declared in multiple base classes: {text}, {smallint}'


def test_definition_flow_detects_empty_table_definition() -> None:
    try:
        class test1(table):
            pass

    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-existing-columns-node')
        assert error is not None
        assert str(error) == "Class <class 'test_table_definition.test_definition_flow_detects_empty_table_definition.<locals>.test1'> must define columns."


# table_index,\
# table_unique_index,\
# table_primary_key,\
# table_foreign_key,\
# default_nextval
def test_definition_flow_detects_repeated_metadata_instances() -> None:
    try:
        class test1(table):
            field: Annotated[integer, table_primary_key(name='test'), table_primary_key(name='test2')]
        assert False
    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-unique-metadata-types-node')
        assert error is not None
        assert str(error) == f'Metadata type {table_primary_key} can only appear once in field declaration'

    try:
        class test1(table):
            field: Annotated[integer, default_value(1), default_value(2)]
        assert False
    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-unique-metadata-types-node')
        assert error is not None
        assert str(error) == f'Metadata type {default_value} can only appear once in field declaration'

    try:
        class test_seq(smallint_sequence):
            pass

        class test1(table):
            field: Annotated[integer, default_nextval(seq=test_seq)]
        assert False
    except TypeError as e:
        assert str(e) == 'Sequence type must match annotated type'

    try:
        class test_seq(smallint_sequence):
            pass

        class test1(table):
            field: Annotated[smallint, default_nextval(seq=test_seq), default_nextval(seq=test_seq)]
        assert False
    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-unique-metadata-types-node')
        assert error is not None
        assert str(error) == f'Metadata type {default_nextval} can only appear once in field declaration'

    try:
        class test1(table):
            field: Annotated[smallint, comment('test'), comment('tes2')]
        assert False
    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-unique-metadata-types-node')
        assert error is not None
        assert str(error) == f'Metadata type {comment} can only appear once in field declaration'

    try:
        class test2(table):
            field1: Annotated[smallint,
                              table_primary_key(name='test')]

        class test1(table):
            field: Annotated[smallint,
                             table_foreign_key(name='test',
                                                  other_class=test2,
                                                  other_class_column_name='field1'),
                             table_foreign_key(name='test2',
                                                  other_class=test2,
                                                  other_class_column_name='field1'),]
        assert False
    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-unique-metadata-types-node')
        assert error is not None
        assert str(error) == f'Metadata type {table_foreign_key} can only appear once in field declaration'

def test_definition_flow_detects_mutually_exclusive_metadata_types() -> None:
    try:
        class test_seq(smallint_sequence):
            pass

        class test(table):
            field1: Annotated[smallint,
                              default_value(2),
                              default_nextval(seq=test_seq)]

        assert False
    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-mutually-exclusive-metadata-node')
        assert error is not None
        assert str(error) == f'Field field1 described by two mutually exclusive metadata instances: {default_nextval(seq=test_seq)} and {default_value(2)}'


def test_definition_flow_detects_invalid_metadata_types() -> None:
    try:
        class test2(table):
            field1: Annotated[smallint,
                              table_primary_key(name='test')]

        class test_seq(smallint_sequence):
            pass

        class test1(table):
            field1: Annotated[smallint,
                              check(name='test', predicate=this()>literal(0)),
                              default_nextval(seq=test_seq),
                              table_primary_key(name='test'),
                              comment('TEST'),
                              table_index(name='test'),
                              table_unique_index(name='test'),
                              table_foreign_key(name='test',
                                                   other_class=test2,
                                                   other_class_column_name='field1'),]
    except Exception as e:
        print(str(e))
        assert False

    try:
        @dataclass
        class test2:
            field1: str

        class test1(table):
            field1: Annotated[smallint,
                              test2('test')]
        assert False
    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-restricted-metadata-types-node')
        assert error is not None
        assert str(error) == "Invalid metadata type <class 'test_table_definition.test_definition_flow_detects_invalid_metadata_types.<locals>.test2'> in field1 declaration"


def test_foreign_key_definition_correctly_extracted() -> None:
    # NOTE test that referenced columns types are correctly validated
    try:
        class test2(table):
            field1: Annotated[integer,
                              table_primary_key(name='test')]

        class test1(table):
            field: Annotated[smallint,
                             table_foreign_key(name='test2',
                                                  other_class=test2,
                                                  other_class_column_name='field1')]
    except TypeError as e:
        assert str(e) == "Foreign key column field type must match with field1 in <class 'test_table_definition.test_foreign_key_definition_correctly_extracted.<locals>.test2'> definition"

    try:
        class test2(table):
            field3: Annotated[integer,
                              table_primary_key(name='test')]

        class test1(table):
            field: Annotated[smallint,
                             table_foreign_key(name='test2',
                                                  other_class=test2,
                                                  other_class_column_name='field1')]
    except TypeError as e:
        assert str(e) == "Foreign key column field1 must exist in <class 'test_table_definition.test_foreign_key_definition_correctly_extracted.<locals>.test2'> definition"

    # NOTE test that foreign keys are not inherited
    class test1(table):
        field1: Annotated[smallint,
                          table_primary_key(name='test')]

    class test2(table):
        field: Annotated[smallint,
                         table_foreign_key(name='test2',
                                              other_class=test1,
                                              other_class_column_name='field1')]

    class test3(test2):
        pass

    def2 = test2.__pg_definition()
    def3 = test3.__pg_definition()

    assert def2['foreign_keys'] is not None
    assert len(def2['foreign_keys']) == 1

    assert def2['foreign_keys'][0]['other_class'] == test1
    assert set([f[1] for f in def2['foreign_keys'][0]['constrained_column_pairs']]) == set(('field1', ))
    assert set([f[0] for f in def2['foreign_keys'][0]['constrained_column_pairs']]) == set(('field', ))
    assert def2['foreign_keys'][0]['on_update'] == table_foreign_key_action.NO_ACTION
    assert def2['foreign_keys'][0]['on_delete'] == table_foreign_key_action.NO_ACTION
    assert def2['foreign_keys'][0]['name'] == 'test2'

    assert def3['foreign_keys'] is None
    assert extract_first_instance_from_field_metadata(test3.model_fields['field'], table_foreign_key) is None

    # NOTE test that final definition contains expected data
    # NOTE test that foreign keys are correctly grouped by name in final definition
    class test4(table):
        t4_field1: Annotated[smallint,
                             table_primary_key(name='test')]
        t4_field2: Annotated[text,
                             table_primary_key(name='test')]

    class test5(table):
        t5_field1: Annotated[smallint,
                             table_foreign_key(name='test2',
                                                  other_class=test4,
                                                  other_class_column_name='t4_field1')]
        t5_field2: Annotated[text,
                             table_foreign_key(name='test2',
                                                  other_class=test4,
                                                  other_class_column_name='t4_field2')]

    def5 = test5.__pg_definition()
    assert def5['foreign_keys'][0]['other_class'] == test4
    assert set([f[1] for f in def5['foreign_keys'][0]['constrained_column_pairs']]) == set(('t4_field1', 't4_field2'))
    assert set([f[0] for f in def5['foreign_keys'][0]['constrained_column_pairs']]) == set(('t5_field1', 't5_field2'))
    assert def5['foreign_keys'][0]['on_update'] == table_foreign_key_action.NO_ACTION
    assert def5['foreign_keys'][0]['on_delete'] == table_foreign_key_action.NO_ACTION
    assert def5['foreign_keys'][0]['name'] == 'test2'

    # NOTE test that validates that all fields pointed by foreign keys participate in unique index or primary key
    try:
        class test6(table):
            t6_field1: smallint
            t6_field2: Annotated[text,
                                 table_primary_key(name='test')]

        class test7(table):
            t7_field1: Annotated[smallint,
                                 table_foreign_key(name='test2',
                                                      other_class=test6,
                                                      other_class_column_name='t6_field1')]
            t7_field2: Annotated[text,
                                 table_foreign_key(name='test2',
                                                      other_class=test6,
                                                      other_class_column_name='t6_field2')]
        assert False
    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('table-definition-flow',
                                                         'table-extract-foreign-keys-node')
        assert error is not None
        print(str(error))
        assert str(error) == "Foreign key test2 error: Other class <class 'test_table_definition.test_foreign_key_definition_correctly_extracted.<locals>.test6'> must define any ('unique_indexes', 'primary_key') constraint over referenced columns {'t6_field1', 't6_field2'}" or \
            "Foreign key test2 error: Other class <class 'test_table_definition.test_foreign_key_definition_correctly_extracted.<locals>.test6'> must define any ('unique_indexes', 'primary_key') constraint over referenced columns {'t6_field2', 't6_field1'}"

    try:
        class test6(table):
            t6_field1: smallint
            t6_field2: text

        class test7(table):
            t7_field1: Annotated[smallint,
                                 table_foreign_key(name='test2',
                                                      other_class=test6,
                                                      other_class_column_name='t6_field1')]
            t7_field2: Annotated[text,
                                 table_foreign_key(name='test2',
                                                      other_class=test6,
                                                      other_class_column_name='t6_field2')]
        assert False
    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('table-definition-flow',
                                                         'table-extract-foreign-keys-node')
        assert error is not None
        assert str(error) == "Foreign key test2 error: Other class <class 'test_table_definition.test_foreign_key_definition_correctly_extracted.<locals>.test6'> must define any ('unique_indexes', 'primary_key') constraint over referenced columns {'t6_field1', 't6_field2'}" or \
            "Foreign key test2 error: Other class <class 'test_table_definition.test_foreign_key_definition_correctly_extracted.<locals>.test6'> must define any ('unique_indexes', 'primary_key') constraint over referenced columns {'t6_field2', 't6_field1'}"

    try:
        class test6(table):
            t6_field1: Annotated[smallint,
                                 table_primary_key(name='test')]
            t6_field2: text

        class test7(table):
            t7_field1: Annotated[smallint,
                                 table_foreign_key(name='test2',
                                                      other_class=test6,
                                                      other_class_column_name='t6_field1')]
            t7_field2: Annotated[text,
                                 table_foreign_key(name='test2',
                                                      other_class=test6,
                                                      other_class_column_name='t6_field2')]
        assert False
    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('table-definition-flow',
                                                         'table-extract-foreign-keys-node')
        assert error is not None
        assert str(error) == "Foreign key test2 error: Other class <class 'test_table_definition.test_foreign_key_definition_correctly_extracted.<locals>.test6'> must define any ('unique_indexes', 'primary_key') constraint over referenced columns {'t6_field1', 't6_field2'}" or \
            "Foreign key test2 error: Other class <class 'test_table_definition.test_foreign_key_definition_correctly_extracted.<locals>.test6'> must define any ('unique_indexes', 'primary_key') constraint over referenced columns {'t6_field2', 't6_field1'}"

# test_foreign_key_definition_correctly_extracted()

def test_primary_key_definition_correctly_extracted() -> None:
    # NOTE test that there can only be one primary key in the definition
    try:
        class test1(table):
            t1_field1: Annotated[smallint,
                                 table_primary_key(name='test')]
            t1_field2: Annotated[smallint,
                                 table_primary_key(name='test2')]
        assert False
    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('table-definition-flow',
                                                         'table-extract-primary-key-node')
        assert error is not None
        assert str(error) == "Multiple primary keys detected for class <class 'test_table_definition.test_primary_key_definition_correctly_extracted.<locals>.test1'>"

    # NOTE test that primary keys are not inherited
    class test1(table):
        t1_field1: Annotated[smallint,
                             table_primary_key(name='test')]
        t1_field2: Annotated[smallint,
                             table_primary_key(name='test')]

    class test2(test1):
        pass

    assert hasattr(test2, '__pg_definition')
    def2 = getattr(test2, '__pg_definition')()
    assert 'primary_key' in def2
    assert def2['primary_key'] is None
    assert extract_first_instance_from_field_metadata(test2.model_fields['t1_field1'], table_primary_key) is None
    assert extract_first_instance_from_field_metadata(test2.model_fields['t1_field2'], table_primary_key) is None

    # NOTE test primary key is correctly grouped by name in final definition
    # NOTE test that primary key final definition is correct
    assert hasattr(test1, '__pg_definition')
    def1 = getattr(test1, '__pg_definition')()
    assert 'primary_key' in def1
    assert def1['primary_key']['name'] == 'test'
    assert def1['primary_key']['column_name'] == set(('t1_field2', 't1_field1'))


def test_index_definition_correctly_extracted() -> None:
    # NOTE test index is correctly grouped by name in final definition
    class test1(table):
        t1_field1: Annotated[smallint,
                             table_index(name='test')]
        t1_field2: Annotated[smallint,
                             table_index(name='test')]
    assert hasattr(test1, '__pg_definition')
    def1 = getattr(test1, '__pg_definition')()
    assert 'indexes' in def1
    assert len(def1['indexes']) == 1
    assert def1['indexes'][0]['column_name'] == set(('t1_field2', 't1_field1'))
    assert def1['indexes'][0]['type'] == table_index_type.BTREE
    assert def1['indexes'][0]['name'] == 'test'
    # NOTE test that columns can appear in several indexes
    class test2(table):
        t2_field1: Annotated[smallint,
                             table_index(name='test'),
                             table_index(name='test1')]
        t2_field2: Annotated[smallint,
                             table_index(name='test')]
        t2_field3: Annotated[smallint,
                             table_index(name='test1')]
    assert hasattr(test2, '__pg_definition')
    def2 = getattr(test2, '__pg_definition')()
    assert 'indexes' in def2
    assert len(def2['indexes']) == 2
    print(def2['indexes'])
    assert any([ix['column_name'] == set(('t2_field2', 't2_field1')) for ix in def2['indexes']])
    assert any([ix['column_name'] == set(('t2_field1', 't2_field3')) for ix in def2['indexes']])
    assert any([ix['name'] == 'test' for ix in def2['indexes']])
    assert any([ix['name'] == 'test1' for ix in def2['indexes']])
    assert all([ix['type'] == table_index_type.BTREE for ix in def2['indexes']])

    # NOTE test that indexes are not inherited
    class test3(test2):
        pass
    assert hasattr(test3, '__pg_definition')
    def3 = getattr(test3, '__pg_definition')()
    assert 'indexes' in def3
    assert def3['indexes'] is None
    assert extract_first_instance_from_field_metadata(test3.model_fields['t2_field1'], table_index) is None
    assert extract_first_instance_from_field_metadata(test3.model_fields['t2_field2'], table_index) is None
    assert extract_first_instance_from_field_metadata(test3.model_fields['t2_field3'], table_index) is None

    try:
        class test4(table):
            t2_field1: Annotated[smallint,
                                table_index(name='test'),
                                table_index(name='test')]
    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-same-type-meta-instances-have-different-names-node')
        assert error is not None
        assert str(error) == 'Metadata definition error in t2_field1: found 2 repeated instances of same type table_index sharing name test.'


def test_unique_index_definition_correctly_extracted() -> None:
    # NOTE test unique index is correctly grouped by name in final definition
    class test1(table):
        t1_field1: Annotated[smallint,
                             table_unique_index(name='test')]
        t1_field2: Annotated[smallint,
                             table_unique_index(name='test')]
    assert hasattr(test1, '__pg_definition')
    def1 = getattr(test1, '__pg_definition')()
    assert 'unique_indexes' in def1
    assert len(def1['unique_indexes']) == 1
    assert def1['unique_indexes'][0]['column_name'] == set(('t1_field2', 't1_field1'))
    assert def1['unique_indexes'][0]['type'] == table_index_type.BTREE
    assert def1['unique_indexes'][0]['name'] == 'test'
    # NOTE test that columns can appear in several indexes
    class test2(table):
        t2_field1: Annotated[smallint,
                             table_unique_index(name='test'),
                             table_unique_index(name='test1')]
        t2_field2: Annotated[smallint,
                             table_unique_index(name='test')]
        t2_field3: Annotated[smallint,
                             table_unique_index(name='test1')]
    assert hasattr(test2, '__pg_definition')
    def2 = getattr(test2, '__pg_definition')()
    assert 'unique_indexes' in def2
    assert len(def2['unique_indexes']) == 2
    assert any([ix['column_name'] == set(('t2_field2', 't2_field1')) for ix in def2['unique_indexes']])
    assert any([ix['column_name'] == set(('t2_field1', 't2_field3')) for ix in def2['unique_indexes']])
    assert any([ix['name'] == 'test' for ix in def2['unique_indexes']])
    assert any([ix['name'] == 'test1' for ix in def2['unique_indexes']])
    assert all([ix['type'] == table_index_type.BTREE for ix in def2['unique_indexes']])

    # NOTE test that unique indexes are not inherited
    class test3(test2):
        pass
    assert hasattr(test3, '__pg_definition')
    def3 = getattr(test3, '__pg_definition')()
    assert 'unique_indexes' in def3
    assert def3['unique_indexes'] is None
    assert extract_first_instance_from_field_metadata(test3.model_fields['t2_field1'], table_unique_index) is None
    assert extract_first_instance_from_field_metadata(test3.model_fields['t2_field2'], table_unique_index) is None
    assert extract_first_instance_from_field_metadata(test3.model_fields['t2_field3'], table_unique_index) is None

    try:
        class test4(table):
            t2_field1: Annotated[smallint,
                                table_unique_index(name='test'),
                                table_unique_index(name='test')]
    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-same-type-meta-instances-have-different-names-node')
        assert error is not None
        assert str(error) == 'Metadata definition error in t2_field1: found 2 repeated instances of same type table_unique_index sharing name test.'


def test_check_definition_correctly_extracted() -> None:
    # NOTE test that check constraints are not inherited
    class test0(table):
        t0_field1: Annotated[smallint,
                             check(name='test', predicate=this() > literal(0))]
    class test1(table):
        t1_field1: Annotated[smallint,
                             check(name='test', predicate=this() < literal(10))]

    class test2(test0, test1):
        pass

    # test0
    assert hasattr(test0, '__pg_definition')
    def0 = getattr(test0, '__pg_definition')()
    assert 'columns' in def0
    assert isinstance(def0['columns'] , list)
    assert len(def0['columns']) == 1
    assert def0['columns'][0]['name'] == 't0_field1'
    assert def0['columns'][0]['type'] == smallint
    assert def0['columns'][0]['comment'] is None
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
    assert isinstance(def1['columns'] , list)
    assert len(def1['columns']) == 1
    assert def1['columns'][0]['name'] == 't1_field1'
    assert def1['columns'][0]['type'] == smallint
    assert def1['columns'][0]['comment'] is None
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
    assert len(def2['columns']) == 0
    assert 'base_classes' in def2
    assert def2['base_classes'] == set((test0, test1, ))
    # NOTE test that check constraints are applied when instancing class
    # NOTE test that parent check constraints are applied when instancing class
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

    class test4(table):
        t4_field1: Annotated[smallint,
                             check(name='test', predicate=this() > literal(0))]
    class test5(table):
        t4_field1: Annotated[smallint,
                             check(name='test', predicate=this() < literal(10))]

    class test6(test4, test5):
        pass

    class test7(test6):
        t4_field1: Annotated[smallint,
                             check(name='test', predicate=this() > literal(5))]
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
        class test4(table):
            t2_field1: Annotated[smallint,
                                 check(name='test', predicate=this() > literal(0)),
                                 check(name='test', predicate=this() > literal(0))]
    except FlowEndException as e:
        error: Optional[FlowNodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-same-type-meta-instances-have-different-names-node')
        assert error is not None
        assert str(error) == 'Metadata definition error in t2_field1: found 2 repeated instances of same type check sharing name test.'


def test_default_values_correctly_extracted() -> None:
    # NOTE test that default values are present in final column definition
    class test0(table):
        t0_field1: Annotated[smallint,
                             default_value(1)]
    # test0
    assert hasattr(test0, '__pg_definition')
    def0 = getattr(test0, '__pg_definition')()
    assert 'columns' in def0
    assert isinstance(def0['columns'], list)
    assert 'default_value' in def0['columns'][0]
    assert isinstance(def0['columns'][0]['default_value'], default_value)
    assert str(def0['columns'][0]['default_value'].default) == '1'

    class test_seq(smallint_sequence):
        pass

    class test1(table):
        t0_field1: Annotated[smallint,
                             default_nextval(seq=test_seq)]


    assert hasattr(test1, '__pg_definition')
    def1 = getattr(test1, '__pg_definition')()
    assert 'columns' in def1
    assert isinstance(def1['columns'], list)
    assert 'default_value' in def1['columns'][0]
    assert isinstance(def1['columns'][0]['default_value'], default_nextval)


def test_comments_correctly_extracted() -> None:
    # NOTE test that comment are present in final definition
    # NOTE test that comments are not inherited from parent classes
    @with_comment('table test comment')
    class test0(table):
        t0_field1: Annotated[smallint,
                             comment('test comment')]
    # test0
    assert hasattr(test0, '__pg_definition')
    def0 = getattr(test0, '__pg_definition')()
    assert 'columns' in def0
    assert isinstance(def0['columns'], list)
    assert 'comment' in def0['columns'][0]
    assert isinstance(def0['columns'][0]['comment'], comment)
    assert def0['columns'][0]['comment'].value == 'test comment'
    assert 'default_value' in def0['columns'][0]
    assert def0['columns'][0]['default_value'] is None
    assert 'comment' in def0
    assert isinstance(def0['comment'], comment)
    assert def0['comment'].value == 'table test comment'

