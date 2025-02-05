import pg_definition as pg
import test_app.backend.cpp.wrapper as tw


class author_id_sequence(pg.sequence, base=pg.catalog.int8):
    pass


@pg.table.primary_key(name='author_pk', columns=('id', ))
@pg.table.serial(column='id', sequence=author_id_sequence)
class author(tw.author, metaclass=pg.table):
    pass


class with_timestamps(tw.with_timestamps, metaclass=pg.table):
    pass


@pg.table.foreign_key(
    name='authorable_author_fk', references=author,
    columns=('author_id', ), referenced_columns=('id', ))
class authored(tw.authored, metaclass=pg.table):
    pass


class post_status(tw.post_status, metaclass=pg.enum):
    pass


class post_id_sequence(pg.sequence, base=pg.catalog.int8):
    pass


@pg.table.serial(column='id', sequence=post_id_sequence)
@pg.table.primary_key(name='post_pk', columns=('id', ))
class post(tw.post, metaclass=pg.table):
    pass


class comment_id_sequence(pg.sequence, base=pg.catalog.int8):
    pass


@pg.table.foreign_key(
    name='comment_post_fk', references=post,
    columns=('post_id', ), referenced_columns=('id', ))
@pg.table.serial(column='post_id', sequence=comment_id_sequence)
@pg.table.primary_key(name='comment_pk', columns=('id', ))
class comment(tw.comment, metaclass=pg.table):
    pass


class comment_post(tw.comment_post, metaclass=pg.composite):
    pass


class composite_author(tw.composite_author, metaclass=pg.composite):
    pass

