
CREATE OR REPLACE FUNCTION mgr_composite(
    p_id bigint
) RETURNS mgr_composite AS $$
BEGIN
    RETURN SELECT * 
        FROM mgr_composite
        WHERE id = p_id
    ;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION mgr_composite(
    p_name text,
    p_schema text
) RETURNS mgr_composite AS $$
DECLARE 
    v_id bigint;
BEGIN
    SELECT id
        INTO v_id
        FROM mgr_composite
        WHERE name = p_name
        AND schema_name = p_schema_name
    ;
    RETURN mgr_composite(v_id);
END;
$$ LANGUAGE plpgsql;
