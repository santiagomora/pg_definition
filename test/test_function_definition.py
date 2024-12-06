import psycopg
from pgdriver import\
    integer,\
    bigint,\
    smallint,\
    real,\
    text,\
    char,\
    double,\
    byte,\
    timestamptz,\
    timetz,\
    date,\
    boolean
from pgdriver import\
    pg_single_result_function,\
    pg_set_returning_function,\
    pg_execute_function,\
    table,\
    composite,\
    bigint_sequence,\
    default_nextval,\
    table_primary_key,\
    table_foreign_key,\
    enums,\
    adapter_registry
from typing_extensions import \
    Annotated
from enum import\
    auto


dsn_test_db: str = 'host=172.18.0.1 dbname=mutzhub port=5432 user=mutzhub password=WtbNMMpX46iynzjVobrh8Qu7omvFIL9JEvbkLYYCpCJNIwDWnBwcVquhk6vXe6En'


class author_id_sequence(bigint_sequence):
    pass


class post_id_sequence(bigint_sequence):
    pass


class comment_id_sequence(bigint_sequence):
    pass


class post_status_enum(enums):
    published = auto()
    waiting_approval = auto()
    draft = auto()


class author(table):
    id: Annotated[bigint, table_primary_key(name='post_pk'),
                  default_nextval(seq=author_id_sequence)]
    name: text


class with_timestamps(table):
    created_at: timestamptz
    updated_at: timestamptz


class authored(table):
    author_id: Annotated[bigint, table_foreign_key(name='authorable_author_fk',
                                                   other_class=author,
                                                   other_class_column_name='id')]
    content: text


class post(authored, with_timestamps):
    id: Annotated[bigint, table_primary_key(name='post_pk'),
                  default_nextval(seq=post_id_sequence)]
    title: text
    status: post_status_enum


class comment(authored, with_timestamps):
    id: Annotated[bigint, table_primary_key(name='comment_pk')]
    post_id: Annotated[bigint, table_foreign_key(name='comment_post_fk',
                                                 other_class=post,
                                                 other_class_column_name='id'),
                       default_nextval(seq=comment_id_sequence)]


class comment_post(composite):
    comment: comment
    post: post


class get_post_by_id(pg_single_result_function[post]):
    pass


class get_post_comments(pg_set_returning_function[comment]):
    pass


class create_post(pg_single_result_function[comment]):
    pass


class create_comment(pg_single_result_function[comment]):
    pass


def test_sql_function_gets_parameters_correctly() -> None:
    # NOTE test that function store post correctly
    with adapter_registry(dsn_test_db) as reg:
        reg.configure_type(integer, "pg_catalog", "integer")
        reg.configure_type(bigint, "pg_catalog", "bigint")
        reg.configure_type(smallint, "pg_catalog", "smallint")
        reg.configure_type(real, "pg_catalog", "real")
        reg.configure_type(text, "pg_catalog", "text")
        reg.configure_type(char, "pg_catalog", '"char"')
        reg.configure_type(double, "pg_catalog", "double precision")
        reg.configure_type(byte, "pg_catalog", '"char"')
        reg.configure_type(timestamptz, "pg_catalog", "timestamptz")
        reg.configure_type(timetz, "pg_catalog", "timetz")
        reg.configure_type(date, "pg_catalog", "date")
        reg.configure_type(boolean, "pg_catalog", "boolean")
        reg.configure_composite(post, 'test', 'post')
        reg.configure_composite(comment, 'test', 'comment')
        reg.configure_composite(comment_post, 'test', 'comment_post')
        reg.configure_enum(post_status_enum, 'test', 'post_status_enum')

    with psycopg.connect(dsn_test_db) as conn:
        p = post(id=1, title='Hola', content='mundo', author_id=2, created_at=timestamptz.now(), updated_at=timestamptz.now(), status=post_status_enum.published)
        c = comment(id=1, post_id=1, created_at=timestamptz.now(), updated_at=timestamptz.now(), author_id=2, content='test comment')
        cm = comment_post(comment=c, post=p)
        res = conn.execute("SELECT pg_typeof(%(post)s), (%(post)s)", {"post": p}).fetchone()
        print(res)

test_sql_function_gets_parameters_correctly()

