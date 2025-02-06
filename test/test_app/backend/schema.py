import core_pg_bindings as pg
from .functions import\
    create_author,\
    get_author_by_id,\
    get_author_posts,\
    get_post_by_id,\
    get_post_comments,\
    create_post,\
    create_comment,\
    as_comment_post
from .types import\
    author_id_sequence,\
    author,\
    with_timestamps,\
    authored,\
    post_status,\
    post_id_sequence,\
    post,\
    comment_id_sequence,\
    comment,\
    comment_post,\
    composite_author


@pg.schema.register_function_path_alias(
    alias='test_functions', current_file_path=__file__,
    function_path='./sql/functions.sql')
class test_app(pg.schema):
    # functions
    create_author: type[create_author] = create_author
    get_author_by_id: type[get_author_by_id] = get_author_by_id
    get_author_posts: type[get_author_posts] = get_author_posts
    get_post_by_id: type[get_post_by_id] = get_post_by_id
    get_post_comments: type[get_post_comments] = get_post_comments
    create_post: type[create_post] = create_post
    create_comment: type[create_comment] = create_comment
    as_comment_post: type[as_comment_post] = as_comment_post
    # sequences
    author_id_sequence: type[author_id_sequence] = author_id_sequence
    post_id_sequence: type[post_id_sequence] = post_id_sequence
    comment_id_sequence: type[comment_id_sequence] = comment_id_sequence
    # enums
    post_status: type[post_status] = post_status
    # tables
    author: type[author] = author
    with_timestamps: type[with_timestamps] = with_timestamps
    authored: type[authored] = authored
    post: type[post] = post
    comment: type[comment] = comment
    # composites
    comment_post: type[comment_post] = comment_post
    composite_author: type[composite_author] = composite_author
