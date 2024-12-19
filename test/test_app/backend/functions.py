import pgdriver as pg
import test_app.backend.types as types


@pg.register_overload({'p_post_id': pg.int8})
class get_post_by_id(pg.single_result_function[types.post]):
    pass


@pg.register_overload({'p_author_id': pg.int8})
class get_author_by_id(pg.single_result_function[types.author]):
    pass


@pg.register_overload({'p_post': types.post})
class get_post_comments(pg.set_returning_function[types.comment]):
    pass


@pg.register_overload({'p_author': types.author})
class get_author_posts(pg.set_returning_function[types.post]):
    pass


@pg.register_overload({'p_author': types.author, 'p_title': pg.text,
                       'p_content': pg.text})
class create_post(pg.single_result_function[types.post]):
    pass


@pg.register_overload({'p_author': types.author, 'p_post': types.post,
                       'p_content': pg.text})
class create_comment(pg.single_result_function[types.comment]):
    pass


@pg.register_overload({'p_post': types.post, 'p_comment': types.comment,
                       'p_description': pg.text, 'p_author': types.author})
class as_comment_post(pg.single_result_function[types.comment_post]):
    pass

