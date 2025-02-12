from .schema import test_app
import core_pg_bindings as pg


@pg.permission.grant.schema.usage(test_app)
class test_app_schema_usage(pg.permission):
    pass


@pg.permission.grant.table.select(test_app.comment)
@pg.permission.grant.table.references(test_app.comment, ('id', ))
class comment_consultation(pg.permission):
    pass


@pg.permission.grant.table.insert(test_app.comment)
@pg.permission.grant.sequence.usage(test_app.comment_id_sequence)
@pg.permission.grant.sequence.update(test_app.comment_id_sequence)
@pg.permission.grant.function.execute(test_app.create_comment)
class comment_creation(pg.permission):
    pass


@pg.permission.grant.table.select(test_app.post)
@pg.permission.grant.function.execute(test_app.get_post_by_id)
class post_consultation(pg.permission):
    pass


@pg.permission.grant.table.insert(test_app.post)
@pg.permission.grant.sequence.usage(test_app.post_id_sequence)
@pg.permission.grant.sequence.update(test_app.post_id_sequence)
@pg.permission.grant.function.execute(test_app.create_post)
class post_creation(pg.permission):
    pass


@pg.permission.grant.table.select(test_app.author)
@pg.permission.grant.function.execute(test_app.get_author_by_id)
@pg.permission.grant.function.execute(test_app.get_author_posts)
class author_consultation(pg.permission):
    pass


class schema_user(test_app_schema_usage):
    pass


class poster(post_consultation, post_creation, author_consultation):
    pass


class commenter(comment_consultation, comment_creation):
    pass
