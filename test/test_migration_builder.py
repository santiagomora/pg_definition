import pgdriver.migration.builder as bd
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


def test_composite_definition_correctly_built() -> None:
    @pg.in_schema('test')
    class test_composite(pg.composite):
        field_1: pg.int4
        field_2: pg.int8
        field_3: pg.timestamptz

    def mod_generator_1(test_composite) -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(test_composite).create()\
            .attribute('field_1').add()\
            .attribute('field_2').add()\
            .attribute('field_3').add()

    double_inclusion(mod_generator_1(test_composite), [
        'CREATE TYPE "test"."test_composite" AS ()',
        'ALTER TYPE "test"."test_composite" ADD ATTRIBUTE "field_1" "pg_catalog"."int4"',
        'ALTER TYPE "test"."test_composite" ADD ATTRIBUTE "field_2" "pg_catalog"."int8"',
        'ALTER TYPE "test"."test_composite" ADD ATTRIBUTE "field_3" "pg_catalog"."timestamptz"'])

    def mod_generator_2(test_composite) -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(test_composite)\
            .rename_from(old_name='old_test_composite')\
            .attribute('field_2').type().set()\
            .attribute('field_3').rename_from(old_name='old_field_3')
        yield bd.drop_composite('test', test_composite.__name__)

    double_inclusion(mod_generator_2(test_composite), [
        'ALTER TYPE "test"."old_test_composite" RENAME TO "test_composite"',
        'ALTER TYPE "test"."test_composite" ALTER ATTRIBUTE "field_2" TYPE "pg_catalog"."int8"',
        'ALTER TYPE "test"."test_composite" RENAME ATTRIBUTE "old_field_3" TO "field_3"',
        'DROP TYPE "test"."test_composite"'])

    try:
        bd.builder(test_composite).attribute('field_1').drop()
    except TypeError as e:
        assert str(e) == 'Error definition_value_is_not_present: "field_1" must not be present in "test_composite" definition'


def test_enum_definition_correctly_built() -> None:
    @pg.in_schema('test')
    class test_enum(pg.enums):
        enum_value_1 = pg.auto()
        enum_value_2 = pg.auto()
        enum_value_3 = pg.auto()
        enum_value_4 = pg.auto()

    def mod_generator_1(test_emum) -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(test_enum).create()\
            .value('enum_value_1').add()\
            .value('enum_value_2').add()\
            .value('enum_value_3').add()\
            .value('enum_value_4').add()

    double_inclusion(mod_generator_1(test_enum), [
        'CREATE TYPE "test"."test_enum" AS ENUM ()',
        'ALTER TYPE "test"."test_enum" ADD VALUE %s',
        'ALTER TYPE "test"."test_enum" ADD VALUE %s',
        'ALTER TYPE "test"."test_enum" ADD VALUE %s',
        'ALTER TYPE "test"."test_enum" ADD VALUE %s'])

    @pg.in_schema('test')
    class test_enum_2(pg.enums):
        enum_value_1 = pg.auto()
        enum_value_2 = pg.auto()
        enum_value_3 = pg.auto()

    def mod_generator_2(test_enum_2) -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(test_enum_2)\
            .value('enum_value_3').add()\
            .value('enum_value_1').rename_from(old_name='enum_value_0')\
            .value('enum_value_2').add()
        # TODO add rename_from clause
        yield bd.drop_enum('test', 'test_enum_2')

    double_inclusion(mod_generator_2(test_enum_2), [
        'ALTER TYPE "test"."test_enum_2" ADD VALUE %s',
        'ALTER TYPE "test"."test_enum_2" RENAME VALUE %s TO %s',
        'ALTER TYPE "test"."test_enum_2" ADD VALUE %s',
        'DROP TYPE "test"."test_enum_2"'])


def test_sequence_definition_correctly_built() -> None:
    @pg.increment(1)
    @pg.min_value(1)
    @pg.max_value(20)
    @pg.in_schema('test')
    class test_sequence(pg.int2_sequence):
        pass

    def mod_generator_1(test_sequence) -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(test_sequence).create()\
            .attribute('min_value').set()\
            .attribute('max_value').set()\
            .attribute('increment').set()

    double_inclusion(mod_generator_1(test_sequence), [
        'CREATE SEQUENCE "test"."test_sequence" AS "pg_catalog"."int2"',
        'ALTER SEQUENCE "test"."test_sequence" MINVALUE %s',
        'ALTER SEQUENCE "test"."test_sequence" MAXVALUE %s',
        'ALTER SEQUENCE "test"."test_sequence" INCREMENT BY %s'])

    @pg.in_schema('test')
    class test_sequence_2(pg.int4_sequence):
        pass

    try:
        bd.builder(test_sequence_2)\
            .attribute('min_value').set()
        assert False
    except TypeError as e:
        assert str(e) == 'Error definition_value_is_present: "min_value" must be present in "test_sequence_2" definition'

    try:
        bd.builder(test_sequence_2)\
            .attribute('max_value').set()
        assert False
    except TypeError as e:
        assert str(e) == 'Error definition_value_is_present: "max_value" must be present in "test_sequence_2" definition'

    try:
        bd.builder(test_sequence_2)\
            .attribute('increment').set()
        assert False
    except TypeError as e:
        assert str(e) == 'Error definition_value_is_present: "increment" must be present in "test_sequence_2" definition'

    def mod_generator_2(test_sequence_2) -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(test_sequence_2)\
            .rename_from(old_name='test_sequence')\
            .type().set()

    double_inclusion(mod_generator_2(test_sequence_2), [
        'ALTER SEQUENCE "test"."test_sequence" RENAME TO "test_sequence_2"',
        'ALTER SEQUENCE "test"."test_sequence_2" AS "pg_catalog"."int4"'])

    @pg.increment(1)
    @pg.min_value(1)
    @pg.max_value(20)
    @pg.in_schema('test')
    class test_sequence_3(pg.int2_sequence):
        pass

    def mod_generator_3(test_sequence_3) -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(test_sequence_3)\
            .rename_from(old_name='test_sequence')\
            .type().set()\
            .attribute('increment').set()\
            .attribute('min_value').set()\
            .attribute('max_value').set()
        yield bd.drop_sequence('test', 'test_sequence_3')

    double_inclusion(mod_generator_3(test_sequence_3), [
        'ALTER SEQUENCE "test"."test_sequence" RENAME TO "test_sequence_3"',
        'ALTER SEQUENCE "test"."test_sequence_3" AS "pg_catalog"."int2"',
        'ALTER SEQUENCE "test"."test_sequence_3" INCREMENT BY %s',
        'ALTER SEQUENCE "test"."test_sequence_3" MINVALUE %s',
        'ALTER SEQUENCE "test"."test_sequence_3" MAXVALUE %s',
        'DROP SEQUENCE "test"."test_sequence_3"'])


def test_domain_definition_correctly_built() -> None:
    @pg.check(name='domain1_gt_0', predicate=pg.this() > pg.literal(0))
    @pg.in_schema('test')
    class domain1(pg.int8):
        pass

    def mod_generator_1(domain1) -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(domain1).create()\
            .constraint('domain1_gt_0').add()

    double_inclusion(mod_generator_1(domain1), [
        'CREATE DOMAIN "test"."domain1" AS "pg_catalog"."int8"',
        'ALTER DOMAIN "test"."domain1" ADD CONSTRAINT "domain1_gt_0" CHECK (VALUE > 0)'])

    def mod_generator_2(domain1) -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(domain1)\
            .constraint('domain1_gt_0').rename_from(old_name='domain1_gt_0_old')

    double_inclusion(mod_generator_2(domain1), [
        'ALTER DOMAIN "test"."domain1" RENAME CONSTRAINT "domain1_gt_0_old" TO "domain1_gt_0"'])

    @pg.in_schema('test')
    class domain2(pg.int8):
        pass

    try:
        bd.builder(domain2).constraint('domain1_gt_0')\
            .rename_from(old_name='domain1_gt_0_old')
        assert False
    except TypeError as e:
        assert str(e) == 'Error definition_value_is_present: "domain1_gt_0" must be present in "domain2" definition'

    try:
        bd.builder(domain1).constraint('domain1_gt_0_old').drop()
        assert False
    except TypeError as e:
        assert str(e) == 'Error definition_value_is_not_present: "domain1_gt_0_old" must not be present in "domain1" definition'


def test_table_definition_correctly_built() -> None:
    @pg.in_schema('test')
    class test_table1(pg.table):
        field_1: pg.int4

    @pg.in_schema('test')
    class test_table2(pg.table):
        field_2: pg.int4

    @pg.in_schema('test')
    class test_table3(test_table1, test_table2):
        field_3: pg.int4
        field_4: pg.timestamptz

    def mod_generator_1(test_table3) -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(test_table3).create()\
            .rename_from(old_name='old_test_table3')\
            .column('field_3').add()\
            .column('field_2').drop()\
            .column('field_4').type().set()\
            .column('field_4').rename_from(old_name='old_field_4')

    double_inclusion(mod_generator_1(test_table3), [
        'CREATE TABLE "test"."test_table3" () INHERITS ("test"."test_table1", "test"."test_table2")',
        'ALTER TABLE "test"."old_test_table3" RENAME TO "test_table3"',
        'ALTER TABLE "test"."test_table3" ADD COLUMN "field_3" "pg_catalog"."int4"',
        'ALTER TABLE "test"."test_table3" DROP COLUMN "field_2"',
        'ALTER TABLE "test"."test_table3" ALTER COLUMN "field_4" TYPE "pg_catalog"."timestamptz"',
        'ALTER TABLE "test"."test_table3" RENAME COLUMN "old_field_4" TO "field_4"'])

    @pg.in_schema('test')
    class test_table4(pg.table):
        field_1: pg.Annotated[pg.int4, pg.meta.default_value(3)]
        field_2: pg.int4

    def mod_generator_2(test_table4) -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(test_table4).create()\
            .column('field_1').default().set()\
            .column('field_2').default().drop()

    double_inclusion(mod_generator_2(test_table4), [
        'CREATE TABLE "test"."test_table4" ()',
        'ALTER TABLE "test"."test_table4" ALTER COLUMN "field_1" SET DEFAULT 3',
        'ALTER TABLE "test"."test_table4" ALTER COLUMN "field_2" DROP DEFAULT'])

    @pg.in_schema('test')
    class test_table6_id_seq(pg.int4_sequence):
        pass

    @pg.in_schema('test')
    @pg.unique_constraint(name='t5_field_1_unique', columns=('field_3', 'field_4', ))
    class test_table5(pg.table):
        field_3: pg.Annotated[pg.int4, pg.meta.default_value(3)]
        field_4: pg.int4

    def mod_generator_3(test_table5) -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(test_table5).create()\
            .column('field_3').add()\
            .column('field_3').default().set()\
            .column('field_4').add()\
            .unique_constraint('t5_field_1_unique').add()

    double_inclusion(mod_generator_3(test_table5), [
        'CREATE TABLE "test"."test_table5" ()',
        'ALTER TABLE "test"."test_table5" ADD COLUMN "field_3" "pg_catalog"."int4"',
        'ALTER TABLE "test"."test_table5" ALTER COLUMN "field_3" SET DEFAULT 3',
        'ALTER TABLE "test"."test_table5" ADD COLUMN "field_4" "pg_catalog"."int4"',
        'ALTER TABLE "test"."test_table5" ADD CONSTRAINT "t5_field_1_unique" UNIQUE ("field_3", "field_4")'])

    @pg.in_schema('test')
    @pg.primary_key(name='t6_field_1_pk', columns=('field_1', 'field_2', ))
    @pg.foreign_key(name='t6_field_1_fk', other_class=test_table5,
                    columns=('field_1', 'field_2', ), other_class_columns=('field_3', 'field_4', ))
    @pg.index(name='t6_field_1_field_2_ix', columns=('field_1', 'field_2'),
              type=pg.index_type.BRIN)
    @pg.index(name='t6_field_1_field_2_ix2', columns=('field_1', ))
    class test_table6(pg.table):
        field_1: pg.Annotated[pg.int4, pg.meta.default_nextval(seq=test_table6_id_seq)]
        field_2: pg.int4

    def mod_generator_4(test_table6) -> Generator[bd.SQLSentenceParams, None, None]:
        yield from bd.builder(test_table6).create()\
            .column('field_1').add()\
            .column('field_1').default().set()\
            .column('field_2').add()\
            .primary_key('t6_field_1_pk').add()\
            .foreign_key('t6_field_1_fk').add()\
            .index('t6_field_1_field_2_ix').create()\
            .index('t6_field_1_field_2_ix').rename_from(old_name='old_t6_field_1_field_2_ix')\
            .index('t6_field_1_field_2_ix2').create()

    double_inclusion(mod_generator_4(test_table6), [
        'CREATE TABLE "test"."test_table6" ()',
        'ALTER TABLE "test"."test_table6" ADD COLUMN "field_1" "pg_catalog"."int4"',
        "ALTER TABLE \"test\".\"test_table6\" ALTER COLUMN \"field_1\" SET DEFAULT nextval(%s)",
        'ALTER TABLE "test"."test_table6" ADD COLUMN "field_2" "pg_catalog"."int4"',
        'ALTER TABLE "test"."test_table6" ADD CONSTRAINT "t6_field_1_pk" PRIMARY KEY ("field_1", "field_2")',
        'ALTER TABLE "test"."test_table6" ADD CONSTRAINT "t6_field_1_fk" FOREIGN KEY ("field_1", "field_2")',
        'CREATE INDEX "t6_field_1_field_2_ix" ON "test"."test_table6" USING BRIN ("field_1", "field_2")',
        'ALTER INDEX "old_t6_field_1_field_2_ix" RENAME TO "t6_field_1_field_2_ix"',
        'CREATE INDEX "t6_field_1_field_2_ix2" ON "test"."test_table6" USING BTREE ("field_1")'])

