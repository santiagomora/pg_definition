from pgdriver import\
    bigint,\
    text,\
    timestamptz,\
    table,\
    composite,\
    bigint_sequence,\
    default_nextval,\
    primary_key,\
    foreign_key,\
    enums
from typing_extensions import \
    Annotated
from enum import\
    auto


class author_id_sequence(bigint_sequence):
    pass


class post_id_sequence(bigint_sequence):
    pass


class comment_id_sequence(bigint_sequence):
    pass


class post_status_enum(enums):
    published = auto()
    waiting_approval = auto()
    draft = auto()


class author(table):
    id: Annotated[bigint, primary_key(name='post_pk'),
                  default_nextval(seq=author_id_sequence)]
    name: text


class with_timestamps(table):
    created_at: timestamptz
    updated_at: timestamptz


class authored(table):
    author_id: Annotated[bigint, foreign_key(name='authorable_author_fk',
                                                   other_class=author,
                                                   other_class_column_name='id')]
    content: text


class post(authored, with_timestamps):
    id: Annotated[bigint, primary_key(name='post_pk'),
                  default_nextval(seq=post_id_sequence)]
    title: text
    status: post_status_enum


class comment(authored, with_timestamps):
    id: Annotated[bigint, primary_key(name='comment_pk')]
    post_id: Annotated[bigint, foreign_key(name='comment_post_fk',
                                                 other_class=post,
                                                 other_class_column_name='id'),
                       default_nextval(seq=comment_id_sequence)]


class comment_post(composite):
    comment: comment
    post: post
    description: text
    author: author
