import pg_definition.builder.schema as bd
import pg_definition as pg
import psycopg
from typing import\
    Generator
import sys
import os
sys.path.append('./')
import test_app


dsn_test_db: str = 'host=172.18.0.1 dbname=mutzhub port=5432 user=mutzhub password=WtbNMMpX46iynzjVobrh8Qu7omvFIL9JEvbkLYYCpCJNIwDWnBwcVquhk6vXe6En'


def double_inclusion(builder: bd.Builder, sentences: list[str]) -> None:
    builder_sentences: list[str] = []
    with psycopg.connect(dsn_test_db) as conn:
        for bs in builder:
            sentence, identifiers, params = bs.sql_sentence_params()
            builder_sentences.append(psycopg.sql.SQL(sentence).format(*identifiers).as_string(conn))
    print(builder_sentences)
    assert(len(builder_sentences) == len(sentences))
    assert all([bs in sentences for bs in builder_sentences])
    assert all([s in builder_sentences for s in sentences])


class _test_composite(pg.composite):
    field_1: pg.int4
    field_2: pg.int8
    field_3: pg.timestamptz


class _test_enum(pg.enums):
    enum_value_1 = pg.auto()
    enum_value_2 = pg.auto()
    enum_value_3 = pg.auto()
    enum_value_4 = pg.auto()


class _test_enum_2(pg.enums):
    enum_value_1 = pg.auto()
    enum_value_2 = pg.auto()
    enum_value_3 = pg.auto()


@pg.increment(1)
@pg.min_value(1)
@pg.max_value(20)
class _test_sequence(pg.int2_sequence):
    pass


class _test_sequence_2(pg.int4_sequence):
    pass


@pg.increment(1)
@pg.min_value(1)
@pg.max_value(20)
class _test_sequence_3(pg.int2_sequence):
    pass


@pg.check(name='_domain1_gt_0', predicate=pg.this() > pg.literal(0))
class _domain1(pg.int8):
    pass


class _domain2(pg.int8):
    pass


class _test_table1(pg.table):
    field_1: pg.int4


class _test_table2(pg.table):
    field_2: pg.int4


class _test_table3(_test_table1, _test_table2):
    field_3: pg.int4
    field_4: pg.timestamptz


class _test_table6_id_seq(pg.int4_sequence):
    pass


@pg.unique_constraint(name='t5_field_1_unique', columns=('field_3', 'field_4', ))
class _test_table5(pg.table):
    field_3: pg.Annotated[pg.int4, pg.meta.default_value(3)]
    field_4: pg.int4


class _test_table4(pg.table):
    field_1: pg.Annotated[pg.int4, pg.meta.default_value(3)]
    field_2: pg.int4


@pg.primary_key(name='t6_field_1_pk', columns=('field_1', 'field_2', ))
@pg.foreign_key(name='t6_field_1_fk', other_class=_test_table5,
                columns=('field_1', 'field_2', ), other_class_columns=('field_3', 'field_4', ))
@pg.index(name='t6_field_1_field_2_ix', columns=('field_1', 'field_2'),
            type=pg.index_type.BRIN)
@pg.index(name='t6_field_1_field_2_ix2', columns=('field_1', ))
class _test_table6(pg.table):
    field_1: pg.Annotated[pg.int4, pg.meta.default_nextval(seq=_test_table6_id_seq)]
    field_2: pg.int4


class _test(pg.schema):
    _test_composite = _test_composite
    _test_enum = _test_enum
    _test_enum_2 = _test_enum_2
    _test_sequence = _test_sequence
    _test_sequence_2 = _test_sequence_2
    _test_sequence_3 = _test_sequence_3
    _domain1 = _domain1
    _domain2 = _domain2
    _test_table1 = _test_table1
    _test_table2 = _test_table2
    _test_table3 = _test_table3
    _test_table6_id_seq = _test_table6_id_seq
    _test_table5 = _test_table5
    _test_table4 = _test_table4
    _test_table6 = _test_table6


def test_composite_definition_correctly_built() -> None:

    def mod_generator_1() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test)\
            .composite('_test_composite').create()\
            .composite('_test_composite').attribute('field_1').add()\
            .composite('_test_composite').attribute('field_2').add()\
            .composite('_test_composite').attribute('field_3').add()

    double_inclusion(mod_generator_1(), [
        'CREATE TYPE "_test"."_test_composite" AS ()',
        'ALTER TYPE "_test"."_test_composite" ADD ATTRIBUTE "field_1" "pg_catalog"."int4"',
        'ALTER TYPE "_test"."_test_composite" ADD ATTRIBUTE "field_2" "pg_catalog"."int8"',
        'ALTER TYPE "_test"."_test_composite" ADD ATTRIBUTE "field_3" "pg_catalog"."timestamptz"'])

    def mod_generator_2() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test)\
            .composite('_test_composite').rename_from(old_name='old__test_composite')\
            .composite('_test_composite').attribute('field_2').type().set()\
            .composite('_test_composite').attribute('field_3').rename_from(old_name='old_field_3')
        yield from bd.builder(_test).composite('old__test_composite').drop()

    double_inclusion(mod_generator_2(), [
        'ALTER TYPE "_test"."old__test_composite" RENAME TO "_test_composite"',
        'ALTER TYPE "_test"."_test_composite" ALTER ATTRIBUTE "field_2" TYPE "pg_catalog"."int8"',
        'ALTER TYPE "_test"."_test_composite" RENAME ATTRIBUTE "old_field_3" TO "field_3"',
        'DROP TYPE "_test"."old__test_composite"'])

    try:
        bd.builder(_test).composite('_test_composite').attribute('field_1').drop()
    except TypeError as e:
        assert str(e) == 'Error definition_value_is_not_present: "field_1" must not be present in "_test_composite" definition'


def test_enum_definition_correctly_built() -> None:
    def mod_generator_1() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test).enum('_test_enum').create()\
            .enum('_test_enum').value('enum_value_1').add()\
            .enum('_test_enum').value('enum_value_2').add()\
            .enum('_test_enum').value('enum_value_3').add()\
            .enum('_test_enum').value('enum_value_4').add()

    double_inclusion(mod_generator_1(), [
        'CREATE TYPE "_test"."_test_enum" AS ENUM ()',
        'ALTER TYPE "_test"."_test_enum" ADD VALUE %s',
        'ALTER TYPE "_test"."_test_enum" ADD VALUE %s',
        'ALTER TYPE "_test"."_test_enum" ADD VALUE %s',
        'ALTER TYPE "_test"."_test_enum" ADD VALUE %s'])

    def mod_generator_2() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test)\
            .enum('_test_enum_2').value('enum_value_3').add()\
            .enum('_test_enum_2').value('enum_value_1').rename_from(old_name='enum_value_0')\
            .enum('_test_enum_2').value('enum_value_2').add()
        # TODO add rename_from clause
        yield from bd.builder(_test).enum('old__test_enum_2').drop()

    double_inclusion(mod_generator_2(), [
        'ALTER TYPE "_test"."_test_enum_2" ADD VALUE %s',
        'ALTER TYPE "_test"."_test_enum_2" RENAME VALUE %s TO %s',
        'ALTER TYPE "_test"."_test_enum_2" ADD VALUE %s',
        'DROP TYPE "_test"."old__test_enum_2"'])


def test_sequence_definition_correctly_built() -> None:

    def mod_generator_1() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test).sequence('_test_sequence').create()\
            .sequence('_test_sequence').attribute('min_value').set()\
            .sequence('_test_sequence').attribute('max_value').set()\
            .sequence('_test_sequence').attribute('increment').set()

    double_inclusion(mod_generator_1(), [
        'CREATE SEQUENCE "_test"."_test_sequence" AS "pg_catalog"."int2"',
        'ALTER SEQUENCE "_test"."_test_sequence" MINVALUE %s',
        'ALTER SEQUENCE "_test"."_test_sequence" MAXVALUE %s',
        'ALTER SEQUENCE "_test"."_test_sequence" INCREMENT BY %s'])

    try:
        bd.builder(_test)\
            .sequence('_test_sequence_2').attribute('min_value').set()
        assert False
    except TypeError as e:
        assert str(e) == 'Error definition_value_is_present: "min_value" must be present in "_test_sequence_2" definition'

    try:
        bd.builder(_test)\
            .sequence('_test_sequence_2').attribute('max_value').set()
        assert False
    except TypeError as e:
        assert str(e) == 'Error definition_value_is_present: "max_value" must be present in "_test_sequence_2" definition'

    try:
        bd.builder(_test)\
            .sequence('_test_sequence_2').attribute('increment').set()
        assert False
    except TypeError as e:
        assert str(e) == 'Error definition_value_is_present: "increment" must be present in "_test_sequence_2" definition'

    def mod_generator_2() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test)\
            .sequence('_test_sequence_2').rename_from(old_name='_test_sequence')\
            .sequence('_test_sequence_2').type().set()

    double_inclusion(mod_generator_2(), [
        'ALTER SEQUENCE "_test"."_test_sequence" RENAME TO "_test_sequence_2"',
        'ALTER SEQUENCE "_test"."_test_sequence_2" AS "pg_catalog"."int4"'])

    def mod_generator_3() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test)\
            .sequence('_test_sequence_3').rename_from(old_name='_test_sequence')\
            .sequence('_test_sequence_3').type().set()\
            .sequence('_test_sequence_3').attribute('increment').set()\
            .sequence('_test_sequence_3').attribute('min_value').set()\
            .sequence('_test_sequence_3').attribute('max_value').set()
        yield from bd.builder(_test).sequence('old__test_sequence_3').drop()

    double_inclusion(mod_generator_3(), [
        'ALTER SEQUENCE "_test"."_test_sequence" RENAME TO "_test_sequence_3"',
        'ALTER SEQUENCE "_test"."_test_sequence_3" AS "pg_catalog"."int2"',
        'ALTER SEQUENCE "_test"."_test_sequence_3" INCREMENT BY %s',
        'ALTER SEQUENCE "_test"."_test_sequence_3" MINVALUE %s',
        'ALTER SEQUENCE "_test"."_test_sequence_3" MAXVALUE %s',
        'DROP SEQUENCE "_test"."old__test_sequence_3"'])


def test_domain_definition_correctly_built() -> None:

    def mod_generator_1() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test)\
            .domain('_domain1').create()\
            .domain('_domain1').constraint('_domain1_gt_0').add()

    double_inclusion(mod_generator_1(), [
        'CREATE DOMAIN "_test"."_domain1" AS "pg_catalog"."int8"',
        'ALTER DOMAIN "_test"."_domain1" ADD CONSTRAINT "_domain1_gt_0" CHECK (VALUE > 0)'])

    def mod_generator_2() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test)\
            .domain('_domain1').constraint('_domain1_gt_0').rename_from(old_name='_domain1_gt_0_old')

    double_inclusion(mod_generator_2(), [
        'ALTER DOMAIN "_test"."_domain1" RENAME CONSTRAINT "_domain1_gt_0_old" TO "_domain1_gt_0"'])

    try:
        bd.builder(_test)\
            .domain('_domain2').constraint('_domain1_gt_0').rename_from(old_name='_domain1_gt_0_old')
        assert False
    except TypeError as e:
        assert str(e) == 'Error definition_value_is_present: "_domain1_gt_0" must be present in "_domain2" definition'

    try:
        bd.builder(_test).domain('_domain1').constraint('_domain1_gt_0_old').drop()
        assert False
    except TypeError as e:
        assert str(e) == 'Error definition_value_is_not_present: "_domain1_gt_0_old" must not be present in "_domain1" definition'


def test_table_definition_correctly_built() -> None:

    def mod_generator_1() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test)\
            .table('_test_table3').create()\
            .table('_test_table3').rename_from(old_name='old__test_table3')\
            .table('_test_table3').column('field_3').add()\
            .table('_test_table3').column('field_2').drop()\
            .table('_test_table3').column('field_4').type().set()\
            .table('_test_table3').column('field_4').rename_from(old_name='old_field_4')

    double_inclusion(mod_generator_1(), [
        'CREATE TABLE "_test"."_test_table3" () INHERITS ("_test"."_test_table1", "_test"."_test_table2")',
        'ALTER TABLE "_test"."old__test_table3" RENAME TO "_test_table3"',
        'ALTER TABLE "_test"."_test_table3" ADD COLUMN "field_3" "pg_catalog"."int4"',
        'ALTER TABLE "_test"."_test_table3" DROP COLUMN "field_2"',
        'ALTER TABLE "_test"."_test_table3" ALTER COLUMN "field_4" TYPE "pg_catalog"."timestamptz"',
        'ALTER TABLE "_test"."_test_table3" RENAME COLUMN "old_field_4" TO "field_4"'])

    def mod_generator_2() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test)\
            .table('_test_table4').create()\
            .table('_test_table4').column('field_1').default().set()\
            .table('_test_table4').column('field_2').default().drop()

    double_inclusion(mod_generator_2(), [
        'CREATE TABLE "_test"."_test_table4" ()',
        'ALTER TABLE "_test"."_test_table4" ALTER COLUMN "field_1" SET DEFAULT 3',
        'ALTER TABLE "_test"."_test_table4" ALTER COLUMN "field_2" DROP DEFAULT'])

    def mod_generator_3() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test)\
            .table('_test_table5').create()\
            .table('_test_table5').column('field_3').add()\
            .table('_test_table5').column('field_3').default().set()\
            .table('_test_table5').column('field_4').add()\
            .table('_test_table5').unique_constraint('t5_field_1_unique').add()

    double_inclusion(mod_generator_3(), [
        'CREATE TABLE "_test"."_test_table5" ()',
        'ALTER TABLE "_test"."_test_table5" ADD COLUMN "field_3" "pg_catalog"."int4"',
        'ALTER TABLE "_test"."_test_table5" ALTER COLUMN "field_3" SET DEFAULT 3',
        'ALTER TABLE "_test"."_test_table5" ADD COLUMN "field_4" "pg_catalog"."int4"',
        'ALTER TABLE "_test"."_test_table5" ADD CONSTRAINT "t5_field_1_unique" UNIQUE ("field_3", "field_4")'])

    def mod_generator_4() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test)\
            .table('_test_table6').create()\
            .table('_test_table6').column('field_1').add()\
            .table('_test_table6').column('field_1').default().set()\
            .table('_test_table6').column('field_2').add()\
            .table('_test_table6').primary_key('t6_field_1_pk').add()\
            .table('_test_table6').foreign_key('t6_field_1_fk').add()\
            .table('_test_table6').index('t6_field_1_field_2_ix').create()\
            .table('_test_table6').index('t6_field_1_field_2_ix').rename_from(old_name='old_t6_field_1_field_2_ix')\
            .table('_test_table6').index('t6_field_1_field_2_ix2').create()

    double_inclusion(mod_generator_4(), [
        'CREATE TABLE "_test"."_test_table6" ()',
        'ALTER TABLE "_test"."_test_table6" ADD COLUMN "field_1" "pg_catalog"."int4"',
        'ALTER TABLE "_test"."_test_table6" ALTER COLUMN "field_1" SET DEFAULT nextval(%s)',
        'ALTER TABLE "_test"."_test_table6" ADD COLUMN "field_2" "pg_catalog"."int4"',
        'ALTER TABLE "_test"."_test_table6" ADD CONSTRAINT "t6_field_1_pk" PRIMARY KEY ("field_1", "field_2")',
        'ALTER TABLE "_test"."_test_table6" ADD CONSTRAINT "t6_field_1_fk" FOREIGN KEY ("field_1", "field_2")',
        'CREATE INDEX "t6_field_1_field_2_ix" ON "_test"."_test_table6" USING BRIN ("field_1", "field_2")',
        'ALTER INDEX "old_t6_field_1_field_2_ix" RENAME TO "t6_field_1_field_2_ix"',
        'CREATE INDEX "t6_field_1_field_2_ix2" ON "_test"."_test_table6" USING BTREE ("field_1")'])


def test_function_loader() -> None:

    def mod_generator_1() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(test_app.test).load_functions(
            ('create_post', 'create_comment', 'get_post_by_id', ),
            from_function_path_alias='test_functions')\
            .function('create_post').create_or_replace()\
            .function('create_comment').create_or_replace()\
            .function('get_post_by_id').create_or_replace()
        yield from bd.builder(test_app.test)\
            .function('get_post_by_id').execute({'p_post_id': 1})

    double_inclusion(mod_generator_1(), [
        "CREATE OR REPLACE FUNCTION test.create_post(\n    p_author  author,\n    p_content text,\n    p_title   text\n) RETURNS post AS $$\nDECLARE\n    v_result post;\nBEGIN\n    INSERT INTO post(author_id, content, title, status)\n    VALUES (p_author.id, p_content, p_title, 'waiting_approval')\n    RETURNING * INTO v_result;\n    RETURN v_result;\nEND;\n$$ LANGUAGE plpgsql;",
        'CREATE OR REPLACE FUNCTION create_comment(\n    p_author  author,\n    p_post    post,\n    p_content text\n) RETURNS comment AS $$\nDECLARE\n    v_result comment;\nBEGIN\n    INSERT INTO comment(author_id, post_id, content)\n    VALUES (p_author.id, p_post.id, p_content)\n    RETURNING * INTO v_result;\n    RETURN v_result;\nEND;\n$$ LANGUAGE plpgsql;',
        'CREATE OR REPLACE FUNCTION test.get_post_by_id(\n    p_post_id int8\n) RETURNS post AS $$\nDECLARE\n    v_result post;\nBEGIN\n    SELECT * FROM post\n        INTO v_result\n        WHERE id = p_post_id\n        LIMIT 1;\n    RETURN v_result;\nEND;\n$$ LANGUAGE plpgsql;',
        'PERFORM test.get_post_by_id(p_post_id := %(p_post_id)s)'])

    def mod_generator_1() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(test_app.test).load_functions(
            ('create_post', ),
            from_function_path_alias='test_functions')\
            .function('create_post').drop_overload({'p_post_id': pg.int2})

    double_inclusion(mod_generator_1(), [
        'DROP FUNCTION "test"."create_post" ("p_post_id" "pg_catalog"."int2")'])
