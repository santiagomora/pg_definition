import pg_definition as pg
import test_app.backend.types as types


@pg.register_function_path_alias(
    alias='test_functions', current_file_path=__file__,
    function_path='./sql/functions.sql')
class test(pg.schema):
    # functions
    # get_post_by_id: type[functions.get_post_by_id] = functions.get_post_by_id
    # get_author_by_id: type[functions.get_author_by_id] = functions.get_author_by_id
    # get_post_comments: type[functions.get_post_comments] = functions.get_post_comments
    # get_author_posts: type[functions.get_author_posts] = functions.get_author_posts
    # create_post: type[functions.create_post] = functions.create_post
    # create_comment: type[functions.create_comment] = functions.create_comment
    # as_comment_post: type[functions.as_comment_post] = functions.as_comment_post
    # sequences
    author_id_sequence: type[types.author_id_sequence] = types.author_id_sequence
    post_id_sequence: type[types.post_id_sequence] = types.post_id_sequence
    comment_id_sequence: type[types.comment_id_sequence] = types.comment_id_sequence
    # enums
    post_status: type[types.post_status] = types.post_status
    # tables
    author: type[types.author] = types.author
    with_timestamps: type[types.with_timestamps] = types.with_timestamps
    authored: type[types.authored] = types.authored
    post: type[types.post] = types.post
    comment: type[types.comment] = types.comment
    # composites
    comment_post: type[types.comment_post] = types.comment_post
