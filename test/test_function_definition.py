import psycopg
import pgdriver as pg
from typing_extensions import\
    Annotated
from typing import\
    Optional
import datetime
import sys
sys.path.append('./')
from test_app.types import\
    post,\
    comment,\
    comment_post,\
    author,\
    post_status_enum
from test_app.functions import\
    get_post_by_id,\
    get_author_by_id,\
    get_post_comments,\
    create_post,\
    create_comment,\
    get_author_posts,\
    as_comment_post
from test_app.extension import\
    test_app_extension as _test_app_extension
import pytest
from pgdriver.definition.extension import\
    base_extension


dsn_test_db: str = 'host=172.18.0.1 dbname=mutzhub port=5432 user=mutzhub password=WtbNMMpX46iynzjVobrh8Qu7omvFIL9JEvbkLYYCpCJNIwDWnBwcVquhk6vXe6En'


def test_function_definition_flow_executed_correctly() -> None:
    # NOTE test definition is correctly extracted
    class test_func(pg.single_result_function[pg.int8]):
        param_1: pg.timestamptz
        param_2: pg.int8

    assert hasattr(test_func, '__pg_definition')
    def0 = getattr(test_func, '__pg_definition')()
    assert 'comment' in def0
    assert def0['comment'] is None
    assert 'name' in def0
    assert def0['name'] == test_func.__name__
    assert 'return_type' in def0
    assert def0['return_type'] is pg.int8
    assert 'arguments' in def0
    assert 'param_1' in def0['arguments']
    assert def0['arguments']['param_1'] == pg.timestamptz
    assert 'param_2' in def0['arguments']
    assert def0['arguments']['param_2'] == pg.int8

    # NOTE test definition flow doesnt allow parameter metadata
    try:
        class incorrect_meta():
            pass

        class incorrect_test_func(pg.single_result_function[pg.int8]):
            param_1: Annotated[pg.timestamptz, incorrect_meta()]
            param_2: pg.int8
    except pg.FlowException as e:
        error: Optional[pg.NodeException] = e.get_error('function-definition-flow',
                                                         'function-validate-restricted-metadata-types-node')
        assert error is not None
        assert str(error) == "Invalid metadata type <class 'test_function_definition.test_function_definition_flow_executed_correctly.<locals>.incorrect_meta'> in param_1 declaration"

    # NOTE test definition flow doesnt allow non pg types
    try:
        class test(pg.single_result_function[pg.int8]):
            field_1: int
            field_2: str
            field_3: float
            field_4: bytes
            field_5: datetime.datetime
            field_6: datetime.time
            field_7: datetime.date
            field_8: bool
        assert False
    except pg.FlowException as e:
        error: Optional[pg.NodeException] = e.get_error('function-definition-flow',
                                                     'function-validate-arguments-base-type-node')
        assert error is not None
        field_errors: list[str] = [
            f'Field field_3 type must be a subclass of {pg.builtin}',
            f'Field field_2 type must be a subclass of {pg.builtin}',
            f'Field field_6 type must be a subclass of {pg.builtin}',
            f'Field field_7 type must be a subclass of {pg.builtin}',
            f'Field field_5 type must be a subclass of {pg.builtin}',
            f'Field field_4 type must be a subclass of {pg.builtin}',
            f'Field field_1 type must be a subclass of {pg.builtin}',
            f'Field field_8 type must be a subclass of {pg.builtin}']
        for err in field_errors:
            assert err in error.error_list

    # NOTE test definition flow allows only pgtypes for arguments
    try:
        class test(pg.single_result_function[pg.int8]):
            field_1: pg.int8
            field_2: pg.int4
            field_3: pg.int2
            field_4: pg.text
            field_5: pg.timestamptz
            field_6: pg.timetz
            field_7: pg.date
            field_8: pg.float4
            field_9: pg.text
            field_10: pg.char
            field_11: pg.float8
            field_12: pg.bytea
            field_13: pg.bool
    except Exception:
        assert False

    # NOTE test definition flow allows only pgtypes for result type
    try:
        class test(pg.single_result_function[int]):
            pass
    except Exception as e:
        error: Optional[pg.NodeException] = e.get_error('function-definition-flow',
                                                         'function-extract-return-type-node')
        assert error is not None
        assert str(error) == f"Function return type must be a valid pg type, received {int}"

    try:
        class test1(pg.single_result_function[pg.int4]):
            pass

        class test2(pg.single_result_function[pg.int2]):
            pass

        class test3(pg.single_result_function[pg.text]):
            pass

        class test4(pg.single_result_function[pg.timestamptz]):
            pass

        class test5(pg.single_result_function[pg.timetz]):
            pass

        class test6(pg.single_result_function[pg.date]):
            pass

        class test7(pg.single_result_function[pg.float4]):
            pass

        class test8(pg.single_result_function[pg.text]):
            pass

        class test9(pg.single_result_function[pg.char]):
            pass

        class test10(pg.single_result_function[pg.float8]):
            pass

        class test11(pg.single_result_function[pg.bytea]):
            pass

        class test12(pg.single_result_function[pg.bool]):
            pass
    except Exception:
        assert False


@pytest.mark.asyncio
async def test_sql_function_gets_parameters_correctly() -> None:
    with pg.adapter_registry(dsn_test_db) as ar:
        base_extension.register_types(ar)
        _test_app_extension.register_types(ar)

    # NOTE test that function store post correctly
    async with await psycopg.AsyncConnection.connect(dsn_test_db) as conn:
        async with conn.cursor() as cur:
            await cur.execute("SET SEARCH_PATH to test;")
            # NOTE test single result function executed correctly
            post_1: post = await get_post_by_id(cur, p_post_id=1)
            assert isinstance(post_1, post)
            assert post_1.content == 'test content 1'
            assert post_1.title == 'test title 1'
            assert post_1.status == post_status_enum.published
            post_1_author: author = await get_author_by_id(
                cur, p_author_id=post_1.author_id)
            assert post_1_author.name == 'author 1'
            assert post_1_author.id == 1

            # NOTE test set returning function executed correctly
            post_comments: list[comment] = [
                c async for c in get_post_comments(
                    cur, p_post=post_1)]
            assert all([isinstance(c, comment) for c in post_comments])
            assert all([c.post_id == 1 for c in post_comments])
            author_posts: list[comment] = [
                c async for c in get_author_posts(
                    cur, p_author=post_1_author)]
            assert all([p.author_id == 1 for p in author_posts])
            new_post: post = await create_post(
                cur, p_author=post_1_author,
                p_content='this is a new post',
                p_title='new post title')
            assert new_post.author_id == post_1_author.id
            assert new_post.content == 'this is a new post'
            assert new_post.title == 'new post title'
            new_post_comment: comment = await create_comment(
                cur, p_author=post_1_author,
                p_content='new post test comment',
                p_post=new_post)
            assert new_post_comment.author_id == post_1_author.id
            assert new_post_comment.content == 'new post test comment'
            assert new_post_comment.post_id == new_post.id
            new_post_comment: comment = await create_comment(
                cur, p_author=post_1_author,
                p_content='(new post test comment)', p_post=new_post)
            cp: comment_post = await as_comment_post(
                cur, p_post=new_post, p_comment=new_post_comment,
                p_description='test description', p_author=post_1_author)
            assert isinstance(cp, comment_post)
            assert isinstance(cp.post, post)
            assert isinstance(cp.comment, comment)
            assert isinstance(cp.description, pg.text)
            assert isinstance(cp.author, author)
