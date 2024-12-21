from test_app import test
import pg_definition as pg


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


class schema_user(test_schema_usage):
    pass


class poster(post_consultation, post_creation, author_consultation):
    pass


class commenter(comment_consultation, comment_creation):
    pass
