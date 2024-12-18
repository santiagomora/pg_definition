

CREATE OR REPLACE FUNCTION get_author_by_id(
    p_author_id int8
) RETURNS author AS $$
DECLARE
    v_result author;
BEGIN
    SELECT * FROM author
        INTO v_result
        WHERE id = p_author_id
        LIMIT 1;
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION get_post_by_id(
    p_post_id int8
) RETURNS post AS $$
DECLARE
    v_result post;
BEGIN
    SELECT * FROM post
        INTO v_result
        WHERE id = p_post_id
        LIMIT 1;
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;


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

