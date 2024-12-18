from test_app._backend import\
    test,\
    roles
import pgdriver as pg
from typing import\
    Generator


__all__ = ['test_app_extension', 'test', 'roles']


class _TestAppExtension(pg.Extension):
    def functions(self) -> Generator[type, None, None]:
        yield self.schema.get_post_by_id
        yield self.schema.get_author_by_id
        yield self.schema.get_post_comments
        yield self.schema.create_post
        yield self.schema.create_comment
        yield self.schema.get_author_posts
        yield self.schema.as_comment_post

    def sequences(self) -> Generator[type, None, None]:
        yield self.schema.author_id_sequence
        yield self.schema.post_id_sequence
        yield self.schema.comment_id_sequence

    def tables(self) -> Generator[type, None, None]:
        yield self.schema.author
        yield self.schema.with_timestamps
        yield self.schema.authored
        yield self.schema.post
        yield self.schema.comment

    def enums(self) -> Generator[type, None, None]:
        yield self.schema.post_status_enum

    def composites(self) -> Generator[type, None, None]:
        yield self.schema.comment_post


test_app_extension = _TestAppExtension(test)

