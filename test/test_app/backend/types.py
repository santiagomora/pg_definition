import pg_definition as pg
import test_app.backend.cpp.wrapper as tw


class author_id_sequence(pg.sequence, base=pg.int8):
    pass


@pg.primary_key(name='author_pk', columns=('id', ))
@pg.serial(column='id', sequence=author_id_sequence)
class author(tw.author, metaclass=pg.table):
    id: pg.int8
    name: pg.text


class with_timestamps(tw.with_timestamps, metaclass=pg.table):
    created_at: pg.timestamptz
    updated_at: pg.timestamptz


@pg.foreign_key(name='authorable_author_fk', references=author,
                columns=('author_id', ), referenced_columns=('id', ))
class authored(tw.authored, metaclass=pg.table):
    author_id: pg.int8
    content: pg.text


class post_status(tw.post_status, metaclass=pg.enum):
    pass


class post_id_sequence(pg.sequence, base=pg.int8):
    pass


@pg.primary_key(name='post_pk', columns=('id', ))
@pg.serial(column='id', sequence=post_id_sequence)
@pg.inherits(authored, with_timestamps)
class post(tw.post, metaclass=pg.table):
    id: pg.int8
    title: pg.text
    status: post_status
    author_id: pg.int8
    content: pg.text
    created_at: pg.timestamptz
    updated_at: pg.timestamptz


class comment_id_sequence(pg.sequence, base=pg.int8):
    pass


@pg.primary_key(name='comment_pk', columns=('id', ))
@pg.foreign_key(name='comment_post_fk', references=post, 
                columns=('post_id', ), referenced_columns=('id', ))
@pg.serial(column='post_id', sequence=comment_id_sequence)
@pg.inherits(authored, with_timestamps)
class comment(tw.comment, metaclass=pg.table):
    id: pg.int8
    post_id: pg.int8
    author_id: pg.int8
    content: pg.text
    created_at: pg.timestamptz
    updated_at: pg.timestamptz


class comment_post(tw.comment_post, metaclass=pg.composite):
    comment: comment
    post: post
    description: pg.text
    author: author


class composite_author(tw.composite_author, metaclass=pg.composite):
    id: pg.int8
    biography: pg.text
    name: pg.text
