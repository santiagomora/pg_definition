import pgdriver.migration.builder.schema as bd
import pgdriver as pg
import psycopg
from typing import\
    Generator

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
        yield from bd.builder(_test).composite('_test_composite').create()\
            .attribute('field_1').add()\
            .attribute('field_2').add()\
            .attribute('field_3').add()

    double_inclusion(mod_generator_1(), [
        'CREATE TYPE "_test"."_test_composite" AS ()',
        'ALTER TYPE "_test"."_test_composite" ADD ATTRIBUTE "field_1" "pg_catalog"."int4"',
        'ALTER TYPE "_test"."_test_composite" ADD ATTRIBUTE "field_2" "pg_catalog"."int8"',
        'ALTER TYPE "_test"."_test_composite" ADD ATTRIBUTE "field_3" "pg_catalog"."timestamptz"'])

    def mod_generator_2() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test).composite('_test_composite')\
            .rename_from(old_name='old__test_composite')\
            .attribute('field_2').type().set()\
            .attribute('field_3').rename_from(old_name='old_field_3')
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
            .value('enum_value_1').add()\
            .value('enum_value_2').add()\
            .value('enum_value_3').add()\
            .value('enum_value_4').add()

    double_inclusion(mod_generator_1(), [
        'CREATE TYPE "_test"."_test_enum" AS ENUM ()',
        'ALTER TYPE "_test"."_test_enum" ADD VALUE %s',
        'ALTER TYPE "_test"."_test_enum" ADD VALUE %s',
        'ALTER TYPE "_test"."_test_enum" ADD VALUE %s',
        'ALTER TYPE "_test"."_test_enum" ADD VALUE %s'])

    def mod_generator_2() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test).enum('_test_enum_2')\
            .value('enum_value_3').add()\
            .value('enum_value_1').rename_from(old_name='enum_value_0')\
            .value('enum_value_2').add()
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
            .attribute('min_value').set()\
            .attribute('max_value').set()\
            .attribute('increment').set()

    double_inclusion(mod_generator_1(), [
        'CREATE SEQUENCE "_test"."_test_sequence" AS "pg_catalog"."int2"',
        'ALTER SEQUENCE "_test"."_test_sequence" MINVALUE %s',
        'ALTER SEQUENCE "_test"."_test_sequence" MAXVALUE %s',
        'ALTER SEQUENCE "_test"."_test_sequence" INCREMENT BY %s'])

    try:
        bd.builder(_test).sequence('_test_sequence_2')\
            .attribute('min_value').set()
        assert False
    except TypeError as e:
        assert str(e) == 'Error definition_value_is_present: "min_value" must be present in "_test_sequence_2" definition'

    try:
        bd.builder(_test).sequence('_test_sequence_2')\
            .attribute('max_value').set()
        assert False
    except TypeError as e:
        assert str(e) == 'Error definition_value_is_present: "max_value" must be present in "_test_sequence_2" definition'

    try:
        bd.builder(_test).sequence('_test_sequence_2')\
            .attribute('increment').set()
        assert False
    except TypeError as e:
        assert str(e) == 'Error definition_value_is_present: "increment" must be present in "_test_sequence_2" definition'

    def mod_generator_2() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test).sequence('_test_sequence_2')\
            .rename_from(old_name='_test_sequence')\
            .type().set()

    double_inclusion(mod_generator_2(), [
        'ALTER SEQUENCE "_test"."_test_sequence" RENAME TO "_test_sequence_2"',
        'ALTER SEQUENCE "_test"."_test_sequence_2" AS "pg_catalog"."int4"'])

    def mod_generator_3() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test).sequence('_test_sequence_3')\
            .rename_from(old_name='_test_sequence')\
            .type().set()\
            .attribute('increment').set()\
            .attribute('min_value').set()\
            .attribute('max_value').set()
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
        yield from bd.builder(_test).domain('_domain1').create()\
            .constraint('_domain1_gt_0').add()

    double_inclusion(mod_generator_1(), [
        'CREATE DOMAIN "_test"."_domain1" AS "pg_catalog"."int8"',
        'ALTER DOMAIN "_test"."_domain1" ADD CONSTRAINT "_domain1_gt_0" CHECK (VALUE > 0)'])

    def mod_generator_2() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test).domain('_domain1')\
            .constraint('_domain1_gt_0').rename_from(old_name='_domain1_gt_0_old')

    double_inclusion(mod_generator_2(), [
        'ALTER DOMAIN "_test"."_domain1" RENAME CONSTRAINT "_domain1_gt_0_old" TO "_domain1_gt_0"'])

    try:
        bd.builder(_test).domain('_domain2').constraint('_domain1_gt_0')\
            .rename_from(old_name='_domain1_gt_0_old')
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
        yield from bd.builder(_test).table('_test_table3').create()\
            .rename_from(old_name='old__test_table3')\
            .column('field_3').add()\
            .column('field_2').drop()\
            .column('field_4').type().set()\
            .column('field_4').rename_from(old_name='old_field_4')

    double_inclusion(mod_generator_1(), [
        'CREATE TABLE "_test"."_test_table3" () INHERITS ("_test"."_test_table1", "_test"."_test_table2")',
        'ALTER TABLE "_test"."old__test_table3" RENAME TO "_test_table3"',
        'ALTER TABLE "_test"."_test_table3" ADD COLUMN "field_3" "pg_catalog"."int4"',
        'ALTER TABLE "_test"."_test_table3" DROP COLUMN "field_2"',
        'ALTER TABLE "_test"."_test_table3" ALTER COLUMN "field_4" TYPE "pg_catalog"."timestamptz"',
        'ALTER TABLE "_test"."_test_table3" RENAME COLUMN "old_field_4" TO "field_4"'])

    def mod_generator_2() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test).table('_test_table4').create()\
            .column('field_1').default().set()\
            .column('field_2').default().drop()

    double_inclusion(mod_generator_2(), [
        'CREATE TABLE "_test"."_test_table4" ()',
        'ALTER TABLE "_test"."_test_table4" ALTER COLUMN "field_1" SET DEFAULT 3',
        'ALTER TABLE "_test"."_test_table4" ALTER COLUMN "field_2" DROP DEFAULT'])

    def mod_generator_3() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test).table('_test_table5').create()\
            .column('field_3').add()\
            .column('field_3').default().set()\
            .column('field_4').add()\
            .unique_constraint('t5_field_1_unique').add()

    double_inclusion(mod_generator_3(), [
        'CREATE TABLE "_test"."_test_table5" ()',
        'ALTER TABLE "_test"."_test_table5" ADD COLUMN "field_3" "pg_catalog"."int4"',
        'ALTER TABLE "_test"."_test_table5" ALTER COLUMN "field_3" SET DEFAULT 3',
        'ALTER TABLE "_test"."_test_table5" ADD COLUMN "field_4" "pg_catalog"."int4"',
        'ALTER TABLE "_test"."_test_table5" ADD CONSTRAINT "t5_field_1_unique" UNIQUE ("field_3", "field_4")'])

    def mod_generator_4() -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(_test).table('_test_table6').create()\
            .column('field_1').add()\
            .column('field_1').default().set()\
            .column('field_2').add()\
            .primary_key('t6_field_1_pk').add()\
            .foreign_key('t6_field_1_fk').add()\
            .index('t6_field_1_field_2_ix').create()\
            .index('t6_field_1_field_2_ix').rename_from(old_name='old_t6_field_1_field_2_ix')\
            .index('t6_field_1_field_2_ix2').create()

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

