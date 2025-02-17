#include "core_pg_bindings/macros/register.hpp"
#include "test_app/database/typing/namespace.hpp"


namespace ta = test_app::database;


// NOTE FUNCTIONS
PG_INVOKABLE_REGISTER_SUBCLASS_REG(TEST_APP_DB_GET_AUTHOR_POSTS);
std::vector<std::string_view> ta::get_author_posts::overloads = {
R"###(
CREATE OR REPLACE FUNCTION get_author_posts(
    p_author author
) RETURNS SETOF post AS $$
BEGIN
    RETURN QUERY
        SELECT * FROM post
        WHERE author_id = p_author.id
    ;
END;
$$ LANGUAGE plpgsql;
)###"
};


PG_INVOKABLE_REGISTER_SUBCLASS_REG(TEST_APP_DB_CREATE_POST);
std::vector<std::string_view> ta::create_post::overloads = {
R"###(
CREATE OR REPLACE FUNCTION create_post(
    p_author  author,
    p_content text,
    p_title   text
) RETURNS post AS $$
DECLARE
    v_result post;
BEGIN
    INSERT INTO post(author_id, content, title, status)
    VALUES (p_author.id, p_content, p_title, 'waiting_approval')
    RETURNING * INTO v_result;
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
)###"
};


PG_INVOKABLE_REGISTER_SUBCLASS_REG(TEST_APP_DB_CREATE_COMMENT);
std::vector<std::string_view> ta::create_comment::overloads = {
R"###(
CREATE OR REPLACE FUNCTION create_comment(
    p_author  author,
    p_post    post,
    p_content text
) RETURNS comment AS $$
DECLARE
    v_result comment;
BEGIN
    INSERT INTO comment(author_id, post_id, content)
    VALUES (p_author.id, p_post.id, p_content)
    RETURNING * INTO v_result;
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
)###"
};


PG_INVOKABLE_REGISTER_SUBCLASS_REG(TEST_APP_DB_GET_POST_COMMENTS);
std::vector<std::string_view> ta::get_post_comments::overloads = {
R"###(
CREATE OR REPLACE FUNCTION get_post_comments(
    p_post post
) RETURNS SETOF comment AS $$
BEGIN
    RETURN QUERY
        SELECT * FROM comment c
        WHERE post_id = p_post.id
    ;
END;
$$ LANGUAGE plpgsql;
)###"
};


PG_INVOKABLE_REGISTER_SUBCLASS_REG(TEST_APP_DB_AS_COMMENT_POST);
std::vector<std::string_view> ta::as_comment_post::overloads = {
R"###(
CREATE OR REPLACE FUNCTION as_comment_post(
    p_post post,
    p_comment comment,
    p_description text,
    p_author author
) RETURNS comment_post AS $$
BEGIN
    RETURN (p_comment, p_post, p_description, p_author)::comment_post;
END;
$$ LANGUAGE plpgsql;
)###"
};


PG_INVOKABLE_REGISTER_SUBCLASS_REG(TEST_APP_DB_CREATE_AUTHOR);
std::vector<std::string_view> ta::create_author::overloads = {
R"###(
CREATE OR REPLACE FUNCTION create_author()
RETURNS author AS $$
DECLARE 
    v_count int8;
    v_author author;
BEGIN
    v_count := nextval('author_id_sequence'::regclass) + 1;
    INSERT INTO author(id, name)
    VALUES (v_count, 'author ' || v_count)
    RETURNING * INTO v_author;
    RETURN v_author;
END;
$$ LANGUAGE plpgsql;
)###"
};

