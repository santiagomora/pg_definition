from pgdriver import\
    single_result_function,\
    set_returning_function,\
    bigint,\
    text
from test_app.types import\
    post,\
    comment,\
    author,\
    comment_post


class get_post_by_id(single_result_function[post]):
    p_post_id: bigint


class get_author_by_id(single_result_function[author]):
    p_author_id: bigint


class get_post_comments(set_returning_function[comment]):
    p_post: post


class get_author_posts(set_returning_function[post]):
    p_author: author


class create_post(single_result_function[post]):
    p_author: author
    p_title: text
    p_content: text


class create_comment(single_result_function[comment]):
    p_author: author
    p_post: post
    p_content: text


class as_comment_post(single_result_function[comment_post]):
    p_post: post
    p_comment: comment
    p_description: text
    p_author: author
