import pgdriver as pg


class author_id_sequence(pg.int8_sequence):
    pass


class post_id_sequence(pg.int8_sequence):
    pass


class comment_id_sequence(pg.int8_sequence):
    pass


class post_status_enum(pg.enums):
    published = pg.auto()
    waiting_approval = pg.auto()
    draft = pg.auto()


@pg.primary_key(name='author_pk', columns=('id', ))
class author(pg.table):
    id: pg.Annotated[pg.int8, pg.meta.default_nextval(seq=author_id_sequence)]
    name: pg.text


class with_timestamps(pg.table):
    created_at: pg.timestamptz
    updated_at: pg.timestamptz


@pg.foreign_key(name='authorable_author_fk', other_class=author,
                columns=('author_id', ), other_class_columns=('id', ))
class authored(pg.table):
    author_id: pg.int8
    content: pg.text


@pg.primary_key(name='post_pk', columns=('id', ))
class post(authored, with_timestamps):
    id: pg.Annotated[pg.int8, pg.meta.default_nextval(seq=post_id_sequence)]
    title: pg.text
    status: post_status_enum


@pg.primary_key(name='comment_pk', columns=('id', ))
@pg.foreign_key(name='comment_post_fk', other_class=post, columns=('post_id', ),
                other_class_columns=('id', ))
class comment(authored, with_timestamps):
    id: pg.int8
    post_id: pg.Annotated[pg.int8, pg.meta.default_nextval(seq=comment_id_sequence)]


class comment_post(pg.composite):
    comment: comment
    post: post
    description: pg.text
    author: author
