import pgdriver as pg
from test_app.types import\
    post,\
    comment,\
    author,\
    comment_post


class get_post_by_id(pg.single_result_function[post]):
    p_post_id: pg.int8


class get_author_by_id(pg.single_result_function[author]):
    p_author_id: pg.int8


class get_post_comments(pg.set_returning_function[comment]):
    p_post: post


class get_author_posts(pg.set_returning_function[post]):
    p_author: author


class create_post(pg.single_result_function[post]):
    p_author: author
    p_title: pg.text
    p_content: pg.text


class create_comment(pg.single_result_function[comment]):
    p_author: author
    p_post: post
    p_content: pg.text


class as_comment_post(pg.single_result_function[comment_post]):
    p_post: post
    p_comment: comment
    p_description: pg.text
    p_author: author
