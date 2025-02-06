import test_app.backend.cpp.wrapper as tw
import core_pg_bindings as pg


class create_author(pg.function[pg.Optional[tw.author]], function=tw.create_author):
    pass


class get_author_by_id(pg.function[pg.Optional[tw.author]], function=tw.get_author_by_id):
    pass


class get_author_posts(pg.function[list[tw.post]], function=tw.get_author_posts):
    pass


class get_post_by_id(pg.function[pg.Optional[tw.post]], function=tw.get_post_by_id):
    pass


class get_post_comments(pg.function[list[tw.comment]], function=tw.get_post_comments):
    pass


class create_post(pg.function[pg.Optional[tw.post]], function=tw.create_post):
    pass


class create_comment(pg.function[pg.Optional[tw.comment]], function=tw.create_comment):
    pass


class as_comment_post(pg.function[pg.Optional[tw.comment_post]], function=tw.as_comment_post):
    pass

