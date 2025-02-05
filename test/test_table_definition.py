import pg_definition as pg
from typing_extensions import\
    Annotated
from typing import\
    Optional,\
    Any
from dataclasses import\
    dataclass
from test_app.backend import test_app as ta
import test_app.backend.cpp.wrapper as tw


def test_table_definition_is_correctly_formed() -> None:

    class with_timestamps(tw.with_timestamps, metaclass=pg.table):
        pass

    assert hasattr(with_timestamps, '_postgres_definition')
    definition: dict[str, Any] = with_timestamps._postgres_definition
    assert 'type' in definition
    assert definition['type'] == with_timestamps
    assert 'bases' in definition
    assert definition['bases'] == tuple()
    assert 'comment' in definition
    assert definition['comment'] is None
    assert 'columns' in definition
    assert any([col['name'] == 'created_at' for col in definition['columns'].values()])
    assert any([col['name'] == 'updated_at' for col in definition['columns'].values()])
    assert all([col['comment'] is None for col in definition['columns'].values()])
    assert all([col['type'] == pg.timestamptz for col in definition['columns'].values()])
    assert 'primary_key' in definition
    assert definition['primary_key'] is None
    assert 'foreign_keys' in definition
    assert definition['foreign_keys'] == {}
    assert 'indexes' in definition
    assert definition['indexes'] == {}

    @pg.table.add_comment(value='test comment')
    @pg.table.add_column_comment(column='created_at', value='test comment')
    class test2(tw.with_timestamps, metaclass=pg.table):
        pass

    assert hasattr(test2, '_postgres_definition')
    definition: dict[str, Any] = test2._postgres_definition
    assert 'type' in definition
    assert definition['type'] == test2
    assert 'bases' in definition
    assert definition['bases'] == tuple()
    assert 'comment' in definition
    assert definition['comment'].value == 'test comment'
    assert 'columns' in definition
    assert any([col['name'] == 'created_at' for col in definition['columns'].values()])
    assert any([col['name'] == 'updated_at' for col in definition['columns'].values()])
    assert all([col['type'] == pg.timestamptz for col in definition['columns'].values()])
    assert definition['columns']['created_at']['comment'].value == 'test comment'
    assert 'primary_key' in definition
    assert definition['primary_key'] is None
    assert 'foreign_keys' in definition
    assert definition['foreign_keys'] == {}
    assert 'indexes' in definition
    assert definition['indexes'] == {}


def test_definition_flow_detects_empty_table_definition() -> None:
    try:
        class test1(pg.table):
            pass

    except pg.FlowException as e:
        error: Optional[pg.NodeException] = e.get_error('table-definition-flow',
                                                         'table-validate-existing-columns-node')
        assert error is not None
        assert str(error) == "Class <class 'test_table_definition.test_definition_flow_detects_empty_table_definition.<locals>.test1'> must define columns."


# def test_definition_flow_detects_mutually_exclusive_metadata_types() -> None:
#     try:
#         class test_seq(pg.sequence, base=pg.int2):
#             pass
# 
#         @pg.serial(column='field1', sequence=test_seq)
#         class test(tw.author, metaclass=pg.table):
#             id: pg.int8
#             name: pg.text
# 
#     except AssertionError:
#         pass


# def test_definition_flow_detects_invalid_metadata_types() -> None:
#     try:
#         @dataclass
#         class test2:
#             field1: str
# 
#         class test1(tw.with_timestamps, metaclass=pg.table):
#             pass
#         assert False
#     except pg.FlowException as e:
#         error: Optional[pg.NodeException] = e.get_error('table-definition-flow',
#                                                          'table-validate-restricted-metadata-types-node')
#         assert error is not None
#         assert str(error) == "Invalid metadata type <class 'test_table_definition.test_definition_flow_detects_invalid_metadata_types.<locals>.test2'> in created_at declaration"


def test_foreign_key_definition_correctly_extracted() -> None:
    # NOTE test that referenced columns types are correctly validated
    # @pg.table.serial(column='id', sequence=ta.author_id_sequence)
    @pg.table.primary_key(name='author_pk', columns=('id', ))
    class author(tw.author, metaclass=pg.table):
        pass
    try:
        @pg.table.foreign_key(
            name='authorable_author_fk', references=author,
            columns=('test', ), referenced_columns=('name', ))
        class authored(tw.authored, metaclass=pg.table):
            pass
        assert False
    except TypeError:
        pass
    try:
        @pg.table.foreign_key(
            name='authorable_author_fk', references=author,
            columns=('author_id', ), referenced_columns=('test', ))
        class authored(tw.authored, metaclass=pg.table):
            pass
        assert False
    except TypeError:
        pass
    try:
        @pg.table.foreign_key(
            name='authorable_author_fk', references=author,
            columns=('author_id', ), referenced_columns=('name', ))
        class authored(tw.authored, metaclass=pg.table):
            pass
        assert False
    except TypeError:
        pass
    try:
        class author2(tw.author, metaclass=pg.table):
            pass
        @pg.table.foreign_key(
            name='authorable_author_fk', references=author2,
            columns=('author_id', ), referenced_columns=('id', ))
        class authored(tw.authored, metaclass=pg.table):
            pass
        assert False
    except TypeError:
        pass
    try:
        @pg.table.foreign_key(
            name='authorable_author_fk', references=author2,
            columns=('author_id', 'content', ), referenced_columns=('id', ))
        class authored(tw.authored, metaclass=pg.table):
            pass
        assert False
    except TypeError:
        pass
    try:
        @pg.table.foreign_key(
            name='authorable_author_fk', references=author,
            columns=('author_id', 'content', ), referenced_columns=('id',))
        class authored(tw.authored, metaclass=pg.table):
            pass
        assert False
    except TypeError:
        pass
    try:
        @pg.table.primary_key(name='author_pk', columns=('id', 'name'))
        class author2(tw.author, metaclass=pg.table):
            pass
        @pg.table.foreign_key(
            name='authorable_author_fk', references=author2,
            columns=('author_id', 'content', ), referenced_columns=('id', ))
        class authored(tw.authored, metaclass=pg.table):
            pass
        assert False
    except TypeError:
        pass
    try:
        @pg.table.primary_key(name='author_pk', columns=('id', ))
        class author2(tw.author, metaclass=pg.table):
            pass
        @pg.table.foreign_key(
            name='authorable_author_fk', references=author2,
            columns=('author_id', 'content', ), referenced_columns=('id', 'name'))
        class authored(tw.authored, metaclass=pg.table):
            pass
        assert False
    except TypeError:
        pass
    try:
        @pg.table.unique_constraint(name='author_pk', columns=('id', 'name'))
        class author2(tw.author, metaclass=pg.table):
            pass
        @pg.table.foreign_key(
            name='authorable_author_fk', references=author2,
            columns=('author_id', 'content', ), referenced_columns=('id', 'name'))
        class authored(tw.authored, metaclass=pg.table):
            pass
    except TypeError:
        assert False
    try:
        @pg.table.primary_key(name='author_pk', columns=('id', 'name'))
        class author2(tw.author, metaclass=pg.table):
            pass
        @pg.table.foreign_key(
            name='authorable_author_fk', references=author2,
            columns=('author_id', 'content', ), referenced_columns=('id', 'name'))
        class authored(tw.authored, metaclass=pg.table):
            pass
    except TypeError:
        assert False
    @pg.table.foreign_key(
        name='authorable_author_fk', references=author,
        columns=('author_id', ), referenced_columns=('id', ))
    class authored(tw.authored, metaclass=pg.table):
        pass
    definition = authored._postgres_definition
    assert definition['foreign_keys']['authorable_author_fk']['references'] == author
    assert definition['foreign_keys']['authorable_author_fk']['on_update'] == pg.table.foreign_key_action.NO_ACTION
    assert definition['foreign_keys']['authorable_author_fk']['on_delete'] == pg.table.foreign_key_action.NO_ACTION
    assert definition['foreign_keys']['authorable_author_fk']['name'] == 'authorable_author_fk'


def test_primary_key_definition_correctly_extracted() -> None:
    # NOTE test that there can only be one primary key in the definition
    try:
        @pg.table.primary_key(name='author_pk', columns=('id', ))
        @pg.table.primary_key(name='author_pk', columns=('id', ))
        class author(tw.author, metaclass=pg.table):
            pass
        assert False
    except TypeError:
        pass
    try:
        @pg.table.primary_key(name='author_pk', columns=('test', ))
        class author(tw.author, metaclass=pg.table):
            pass
        assert False
    except TypeError:
        pass

    @pg.table.primary_key(name='author_pk', columns=('id', 'name',))
    class author(tw.author, metaclass=pg.table):
        pass

    # NOTE test primary key is correctly grouped by name in final definition
    # NOTE test that primary key final definition is correct
    assert hasattr(author, '_postgres_definition')
    def1 = author._postgres_definition
    assert 'primary_key' in def1
    assert def1['primary_key']['name'] == 'author_pk'
    assert def1['primary_key']['columns'] == ('id', 'name',)


def test_index_definition_correctly_extracted() -> None:
    try:
        @pg.table.index(name='test1', columns=('id', ))
        @pg.table.index(name='test1', columns=('id', ))
        class author(tw.author, metaclass=pg.table):
            pass
        assert False
    except TypeError:
        pass
    try:
        @pg.table.index(name='test1', columns=('test', ))
        class author(tw.author, metaclass=pg.table):
            pass
        assert False
    except TypeError:
        pass
    # NOTE test index is correctly grouped by name in final definition
    @pg.table.index(name='author_ix', columns=('id', 'name',))
    class author(tw.author, metaclass=pg.table):
        pass

    assert hasattr(author, '_postgres_definition')
    def1 = author._postgres_definition
    assert 'indexes' in def1
    assert len(def1['indexes']) == 1
    assert def1['indexes']['author_ix']['columns'] == ('id', 'name')
    assert def1['indexes']['author_ix']['type'] == pg.table.index_type.BTREE
    assert def1['indexes']['author_ix']['name'] == 'author_ix'

    # NOTE test that columns can appear in several indexes
    @pg.table.index(name='test', columns=('id', 'name',))
    @pg.table.index(name='test1', columns=('id', ), index_type=pg.table.index_type.BRIN)
    class author2(tw.author, metaclass=pg.table):
        pass

    assert hasattr(author2, '_postgres_definition')
    def2 = author2._postgres_definition
    assert 'indexes' in def2
    assert len(def2['indexes']) == 2
    assert 'test' in def2['indexes']
    assert def2['indexes']['test']['columns'] == ('id', 'name')
    assert def2['indexes']['test']['type'] == pg.table.index_type.BTREE
    assert def2['indexes']['test']['name'] == 'test'
    assert 'test1' in def2['indexes']
    assert def2['indexes']['test1']['columns'] == ('id', )
    assert def2['indexes']['test1']['type'] == pg.table.index_type.BRIN
    assert def2['indexes']['test1']['name'] == 'test1'


def test_unique_constraint_definition_correctly_extracted() -> None:
    try:
        @pg.table.unique_constraint(name='test', columns=('id',))
        @pg.table.unique_constraint(name='test', columns=('id',))
        class author(tw.author, metaclass=pg.table):
            pass
    except TypeError:
        pass

    # NOTE test unique index is correctly grouped by name in final definition
    @pg.table.unique_constraint(name='test', columns=('id', 'name',))
    class author2(tw.author, metaclass=pg.table):
        pass

    assert hasattr(author2, '_postgres_definition')
    def1 = author2._postgres_definition
    assert 'unique_constraints' in def1
    assert isinstance(def1['unique_constraints'], dict)
    assert def1['unique_constraints']['test']['columns'] == ('id', 'name',)
    assert def1['unique_constraints']['test']['name'] == 'test'

    # NOTE test that columns can appear in several indexes
    @pg.table.unique_constraint(name='test', columns=('id', 'name',))
    @pg.table.unique_constraint(name='test1', columns=('id',))
    class author3(tw.author, metaclass=pg.table):
        pass
    assert hasattr(author3, '_postgres_definition')
    def2 = author3._postgres_definition
    assert 'unique_constraints' in def2
    assert len(def2['unique_constraints']) == 2
    assert 'test' in def2['unique_constraints']
    assert def2['unique_constraints']['test']['columns'] == ('id', 'name')
    assert def2['unique_constraints']['test']['name'] == 'test'
    assert 'test1' in def2['unique_constraints']
    assert def2['unique_constraints']['test1']['columns'] == ('id', )
    assert def2['unique_constraints']['test1']['name'] == 'test1'


def test_check_definition_correctly_extracted() -> None:
    # NOTE test that pg.check constraints are not inherited
    @pg.table.set_check_constraint(
        column='author_id', name='test', constraint=pg.this() > pg.literal(0))
    class authored(tw.authored, metaclass=pg.table):
        pass

    @pg.table.set_check_constraint(
        column='author_id', name='test', constraint=pg.this() < pg.literal(10))
    class post(tw.post, metaclass=pg.table):
        pass

    assert hasattr(post, '_postgres_definition')
    def0 = post._postgres_definition
    assert 'columns' in def0
    assert str(def0['columns']['author_id']['check']) == 'author_id < 10'
#     # test1
#     assert hasattr(test1, '_postgres_definition')
#     def1 = test1._postgres_definition
#     assert 'columns' in def1
#     assert isinstance(def1['columns'] , dict)
#     assert len(def1['columns']) == 1
#     assert def1['columns']['t1_field1']['name'] == 't1_field1'
#     assert def1['columns']['t1_field1']['type'] == pg.int2
#     assert def1['columns']['t1_field1']['comment'] is None
#     assert 'check' in def1
#     assert isinstance(def1['check'], dict)
#     assert 'test1_test' in def1['check']
#     assert def1['check']['test1_test'].name == 'test1_test'
#     assert str(def1['check']['test1_test']) == '(t1_field1 < 10)'
#     assert 'bases' in def1
#     assert def1['bases'] is None
#     # test2
#     assert hasattr(test2, '_postgres_definition')
#     def2 = test2._postgres_definition
#     assert 'columns' in def2
#     assert def2['columns'] == {}
#     assert 'bases' in def2
#     assert def2['bases'] == (test0, test1, )
#     # NOTE test that pg.check constraints are applied when instancing class
#     # NOTE test that parent pg.check constraints are applied when instancing class
#     try:
#         test0(t0_field1=-1)
#         assert False
#     except ValueError as e:
#         assert str(e) == '1 validation error for test0\n\
# t0_field1\n\
#   Value error, test0_test: constraint validation failed for value "-1" [type=value_error, input_value=-1, input_type=int]\n\
#     For further information visit https://errors.pydantic.dev/2.10/v/value_error'
#     try:
#         test1(t1_field1=11)
#         assert False
#     except ValueError as e:
#         assert str(e) == '1 validation error for test1\n\
# t1_field1\n\
#   Value error, test1_test: constraint validation failed for value "11" [type=value_error, input_value=11, input_type=int]\n\
#     For further information visit https://errors.pydantic.dev/2.10/v/value_error'
#     try:
#         test2(t0_field1=2, t1_field1=11)
#         assert False
#     except ValueError as e:
#         assert str(e) == '1 validation error for test1\n\
# t1_field1\n\
#   Value error, test1_test: constraint validation failed for value "11" [type=value_error, input_value=11, input_type=int]\n\
#     For further information visit https://errors.pydantic.dev/2.10/v/value_error'
#     try:
#         test2(t0_field1=-1, t1_field1=9)
#         assert False
#     except ValueError as e:
#         assert str(e) == '1 validation error for test0\n\
# t0_field1\n\
#   Value error, test0_test: constraint validation failed for value "-1" [type=value_error, input_value=-1, input_type=int]\n\
#     For further information visit https://errors.pydantic.dev/2.10/v/value_error'
# 
#     class test3(test2):
#         pass
# 
#     try:
#         test3(t0_field1=2, t1_field1=11)
#         assert False
#     except ValueError as e:
#         assert str(e) == '1 validation error for test1\n\
# t1_field1\n\
#   Value error, test1_test: constraint validation failed for value "11" [type=value_error, input_value=11, input_type=int]\n\
#     For further information visit https://errors.pydantic.dev/2.10/v/value_error'
#     try:
#         test3(t0_field1=-1, t1_field1=9)
#         assert False
#     except ValueError as e:
#         assert str(e) == '1 validation error for test0\n\
# t0_field1\n\
#   Value error, test0_test: constraint validation failed for value "-1" [type=value_error, input_value=-1, input_type=int]\n\
#     For further information visit https://errors.pydantic.dev/2.10/v/value_error'
# 
#     class test4(pg.table):
#         t4_field1: Annotated[pg.int2,
#                              pg.check(name='test', predicate=pg.this() > pg.literal(0))]
#     class test5(pg.table):
#         t4_field1: Annotated[pg.int2,
#                              pg.check(name='test', predicate=pg.this() < pg.literal(10))]
# 
#     class test6(test4, test5):
#         pass
# 
#     class test7(test6):
#         t4_field1: Annotated[pg.int2,
#                              pg.check(name='test', predicate=pg.this() > pg.literal(5))]
#     try:
#         test6(t4_field1=11)
#         assert False
#     except ValueError as e:
#         assert str(e) == '1 validation error for test5\n\
# t4_field1\n\
#   Value error, test5_test: constraint validation failed for value "11" [type=value_error, input_value=11, input_type=int]\n\
#     For further information visit https://errors.pydantic.dev/2.10/v/value_error'
#     try:
#         test6(t4_field1=-1)
#         assert False
#     except ValueError as e:
#         assert str(e) == '1 validation error for test4\n\
# t4_field1\n\
#   Value error, test4_test: constraint validation failed for value "-1" [type=value_error, input_value=-1, input_type=int]\n\
#     For further information visit https://errors.pydantic.dev/2.10/v/value_error'
# 
#     try:
#         test7(t4_field1=11)
#         assert False
#     except ValueError as e:
#         assert str(e) == '1 validation error for test5\n\
# t4_field1\n\
#   Value error, test5_test: constraint validation failed for value "11" [type=value_error, input_value=11, input_type=int]\n\
#     For further information visit https://errors.pydantic.dev/2.10/v/value_error'
#     try:
#         test7(t4_field1=3)
#         assert False
#     except ValueError as e:
#         assert str(e) == '1 validation error for test7\n\
# t4_field1\n\
#   Value error, test7_test: constraint validation failed for value "3" [type=value_error, input_value=3, input_type=int]\n\
#     For further information visit https://errors.pydantic.dev/2.10/v/value_error'
# 
#     try:
#         class test4(pg.table):
#             t2_field1: Annotated[pg.int2,
#                                  pg.check(name='test', predicate=pg.this() > pg.literal(0)),
#                                  pg.check(name='test', predicate=pg.this() > pg.literal(0))]
#     except pg.FlowException as e:
#         error: Optional[pg.NodeException] = e.get_error('table-definition-flow',
#                                                          'table-validate-same-type-meta-instances-have-different-names-node')
#         assert error is not None
#         assert str(error) == 'Metadata definition error in t2_field1: found 2 repeated instances of same type check sharing name test.'


def test_comments_correctly_extracted() -> None:
    # NOTE test that pg.comment are present in final definition
    @pg.table.add_column_comment(column='id', value='test comment')
    @pg.table.add_comment(value='table test comment')
    class author(tw.author, metaclass=pg.table):
        pass
    assert hasattr(author, '_postgres_definition')
    def0 = author._postgres_definition
    assert 'columns' in def0
    assert isinstance(def0['columns'], dict)
    assert 'comment' in def0['columns']['id']
    assert hasattr(def0['columns']['id']['comment'], 'value')
    assert def0['columns']['id']['comment'].value == 'test comment'
    assert 'default' in def0['columns']['id']
    assert def0['columns']['id']['default'] is pg.Undefined
    assert 'comment' in def0
    assert hasattr(def0['comment'], 'value')
    assert def0['comment'].value == 'table test comment'


def test_default_values() -> None:
    @pg.table.set_default(column='name', default='table test comment')
    @pg.table.set_default(column='id', default=1)
    class author(tw.author, metaclass=pg.table):
        pass
    a = author()
    assert a.id == 1
    assert a.name == 'table test comment'

    assert hasattr(author, '_postgres_definition')
    def0 = author._postgres_definition
    assert 'columns' in def0
    assert isinstance(def0['columns'], dict)
    assert 'default' in def0['columns']['id']
    assert isinstance(def0['columns']['id']['default']._lit, pg.int8)
    assert def0['columns']['id']['default']._lit == 1
    assert 'default' in def0['columns']['name']
    assert isinstance(def0['columns']['name']['default']._lit, pg.text)
    assert def0['columns']['name']['default']._lit == 'table test comment'

    class test_seq(pg.sequence, base=pg.int8):
        pass

    @pg.table.serial(column='id', sequence=test_seq)
    class test1(tw.author, metaclass=pg.table):
        pass

    assert hasattr(test1, '_postgres_definition')
    def1 = test1._postgres_definition
    assert 'columns' in def1
    assert isinstance(def1['columns'], dict)
    assert 'default' in def1['columns']['id']
    assert isinstance(def1['columns']['id']['default'], pg.sequence.nextval)

