import pgdriver as pg
import test_app._backend.types as types


class get_post_by_id(pg.single_result_function[types.post]):
    p_post_id: pg.int8


class get_author_by_id(pg.single_result_function[types.author]):
    p_author_id: pg.int8


class get_post_comments(pg.set_returning_function[types.comment]):
    p_post: types.post


class get_author_posts(pg.set_returning_function[types.post]):
    p_author: types.author


class create_post(pg.single_result_function[types.post]):
    p_author: types.author
    p_title: pg.text
    p_content: pg.text


class create_comment(pg.single_result_function[types.comment]):
    p_author: types.author
    p_post: types.post
    p_content: pg.text


class as_comment_post(pg.single_result_function[types.comment_post]):
    p_post: types.post
    p_comment: types.comment
    p_description: pg.text
    p_author: types.author
