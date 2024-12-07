from .types import\
    post,\
    author,\
    comment,\
    with_timestamps,\
    authored,\
    comment_post,\
    post_status_enum,\
    author_id_sequence,\
    post_id_sequence,\
    comment_id_sequence
from .functions import\
    get_post_by_id,\
    get_post_comments,\
    create_post,\
    create_comment,\
    get_author_by_id,\
    get_author_posts,\
    as_comment_post
from typing import\
    Generator
import pgdriver as pg


__all__ = ['test_app_extension']


class _TestAppExtension(pg.Extension):
    def functions(self) -> Generator[tuple[type, str, str], None, None]:
        yield get_post_by_id
        yield get_author_by_id
        yield get_post_comments
        yield create_post
        yield create_comment
        yield get_author_posts
        yield as_comment_post

    def sequences(self) -> Generator[tuple[type, str, str], None, None]:
        yield author_id_sequence
        yield post_id_sequence
        yield comment_id_sequence

    def tables(self) -> Generator[tuple[type, str, str], None, None]:
        yield author
        yield with_timestamps
        yield authored
        yield post
        yield comment

    def enums(self) -> Generator[tuple[type, str, str], None, None]:
        yield post_status_enum

    def composites(self) -> Generator[tuple[type, str, str], None, None]:
        yield comment_post


test_app_extension = _TestAppExtension('test')
