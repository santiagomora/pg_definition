import psycopg
from pgdriver import\
    adapter_registry,\
    builtin,\
    bigint,\
    integer,\
    smallint,\
    single_result_function,\
    text,\
    timestamptz,\
    timetz,\
    date,\
    real,\
    char,\
    double,\
    byte,\
    boolean
from typing_extensions import\
    Annotated
from pgdriver.definition.common.flow import\
    FlowException,\
    NodeException
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
from pgdriver.extension import\
    base_extension


dsn_test_db: str = 'host=172.18.0.1 dbname=mutzhub port=5432 user=mutzhub password=WtbNMMpX46iynzjVobrh8Qu7omvFIL9JEvbkLYYCpCJNIwDWnBwcVquhk6vXe6En'


def test_function_definition_flow_executed_correctly() -> None:
    # NOTE test definition is correctly extracted
    class test_func(single_result_function[bigint]):
        param_1: timestamptz
        param_2: bigint

    assert hasattr(test_func, '__pg_definition')
    def0 = getattr(test_func, '__pg_definition')()
    assert 'comment' in def0
    assert def0['comment'] is None
    assert 'name' in def0
    assert def0['name'] == test_func.__name__
    assert 'return_type' in def0
    assert def0['return_type'] is bigint
    assert 'arguments' in def0
    assert 'param_1' in def0['arguments']
    assert def0['arguments']['param_1'] == timestamptz
    assert 'param_2' in def0['arguments']
    assert def0['arguments']['param_2'] == bigint

    # NOTE test definition flow doesnt allow parameter metadata
    try:
        class incorrect_meta():
            pass

        class incorrect_test_func(single_result_function[bigint]):
            param_1: Annotated[timestamptz, incorrect_meta()]
            param_2: bigint
    except FlowException as e:
        error: Optional[NodeException] = e.get_error('function-definition-flow',
                                                         'function-validate-restricted-metadata-types-node')
        assert error is not None
        assert str(error) == "Invalid metadata type <class 'test_function_definition.test_function_definition_flow_executed_correctly.<locals>.incorrect_meta'> in param_1 declaration"

    # NOTE test definition flow doesnt allow non pg types
    try:
        class test(single_result_function[bigint]):
            field_1: int
            field_2: str
            field_3: float
            field_4: bytes
            field_5: datetime.datetime
            field_6: datetime.time
            field_7: datetime.date
            field_8: bool
        assert False
    except FlowException as e:
        error: Optional[NodeException] = e.get_error('function-definition-flow',
                                                     'function-validate-arguments-base-type-node')
        assert error is not None
        field_errors: list[str] = [
            f'Field field_3 type must be a subclass of {builtin}',
            f'Field field_2 type must be a subclass of {builtin}',
            f'Field field_6 type must be a subclass of {builtin}',
            f'Field field_7 type must be a subclass of {builtin}',
            f'Field field_5 type must be a subclass of {builtin}',
            f'Field field_4 type must be a subclass of {builtin}',
            f'Field field_1 type must be a subclass of {builtin}',
            f'Field field_8 type must be a subclass of {builtin}']
        for err in field_errors:
            assert err in error.error_list

    # NOTE test definition flow allows only pgtypes for arguments
    try:
        class test(single_result_function[bigint]):
            field_1: bigint
            field_2: integer
            field_3: smallint
            field_4: text
            field_5: timestamptz
            field_6: timetz
            field_7: date
            field_8: real
            field_9: text
            field_10: char
            field_11: double
            field_12: byte
            field_13: boolean
    except Exception:
        assert False

    # NOTE test definition flow allows only pgtypes for result type
    try:
        class test(single_result_function[int]):
            pass
    except Exception as e:
        error: Optional[NodeException] = e.get_error('function-definition-flow',
                                                         'function-extract-return-type-node')
        assert error is not None
        assert str(error) == f"Function return type must be a valid pg type, received {int}"

    try:
        class test1(single_result_function[integer]):
            pass

        class test2(single_result_function[smallint]):
            pass

        class test3(single_result_function[text]):
            pass

        class test4(single_result_function[timestamptz]):
            pass

        class test5(single_result_function[timetz]):
            pass

        class test6(single_result_function[date]):
            pass

        class test7(single_result_function[real]):
            pass

        class test8(single_result_function[text]):
            pass

        class test9(single_result_function[char]):
            pass

        class test10(single_result_function[double]):
            pass

        class test11(single_result_function[byte]):
            pass

        class test12(single_result_function[boolean]):
            pass
    except Exception:
        assert False


@pytest.mark.asyncio
async def test_sql_function_gets_parameters_correctly() -> None:
    with adapter_registry(dsn_test_db) as ar:
        _test_app_extension.register_types(ar)
        base_extension.register_types(ar)

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
            new_post_comment_2: comment = await create_comment(
                cur, p_author=post_1_author,
                p_content='(new post test comment)', p_post=new_post)
            cp: comment_post = await as_comment_post(
                cur, p_post=new_post, p_comment=new_post_comment,
                p_description='test description', p_author=post_1_author)
            assert isinstance(cp, comment_post)
            assert isinstance(cp.post, post)
            assert isinstance(cp.comment, comment)
            assert isinstance(cp.description, text)
            assert isinstance(cp.author, author)
