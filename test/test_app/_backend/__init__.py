import pgdriver as pg
import test_app._backend.types as types
import test_app._backend.functions as functions


class test(pg.schema):
    # functions
    get_post_by_id = functions.get_post_by_id
    get_author_by_id = functions.get_author_by_id
    get_post_comments = functions.get_post_comments
    get_author_posts = functions.get_author_posts
    create_post = functions.create_post
    create_comment = functions.create_comment
    as_comment_post = functions.as_comment_post
    # types
    author_id_sequence = types.author_id_sequence
    post_id_sequence = types.post_id_sequence
    comment_id_sequence = types.comment_id_sequence
    post_status_enum = types.post_status_enum
    author = types.author
    with_timestamps = types.with_timestamps
    authored = types.authored
    post = types.post
    comment = types.comment
    comment_post = types.comment_post


@pg.grant.schema.usage(test)
class test_schema_usage(pg.permission):
    pass


@pg.grant.table.select(test.comment)
@pg.grant.table.references(test.comment, ('id', ))
class comment_consultation(pg.permission):
    pass


@pg.grant.table.insert(test.comment)
@pg.grant.sequence.usage(test.comment_id_sequence)
@pg.grant.sequence.update(test.comment_id_sequence)
@pg.grant.function.execute(test.create_comment)
class comment_creation(pg.permission):
    pass


@pg.grant.table.select(test.post)
@pg.grant.function.execute(test.get_post_by_id)
class post_consultation(pg.permission):
    pass


@pg.grant.table.insert(test.post)
@pg.grant.sequence.usage(test.post_id_sequence)
@pg.grant.sequence.update(test.post_id_sequence)
@pg.grant.function.execute(test.create_post)
class post_creation(pg.permission):
    pass


@pg.grant.table.select(test.author)
@pg.grant.function.execute(test.get_author_by_id)
@pg.grant.function.execute(test.get_author_posts)
class author_consultation(pg.permission):
    pass


class roles:
    class schema_user(test_schema_usage):
        pass

    class poster(post_consultation, post_creation, author_consultation):
        pass

    class commenter(comment_consultation, comment_creation):
        pass
