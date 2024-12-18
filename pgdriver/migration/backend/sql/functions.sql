

CREATE OR REPLACE FUNCTION mgr_get_next_migration_id(
    p_id int8,
    p_datafix_file_name: pg.text,
    p_migration_file_name: pg.text
) RETURNS mgr_migration AS $$
DECLARE
    v_last_migration_id int8;
    v_generated_name text;
    v_current_date timestamptz;
    v_result mgr_migration;
    v_extension text := '.py';
BEGIN
    v_last_migration_id := currval('mgr_migration_id_seq') + 1;
    v_current_date := now() AT TIME ZONE 'UTC';
    IF p_with_datafix THEN
        v_extension := ''
    END IF;
    v_generated_name := format('migration_%s_%s%s', v_last_migration_id, to_char(v_current_date, 'YYYYMMDD'), v_extension);
    INSERT INTO mgr_migration(with_datafix, generated_name, created_at)
    VALUES (p_with_datafix, v_generated_name, v_current_date)
    RETURNING * INTO v_result;
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION mgr_generate_migration(
    p_id int8,
    p_datafix_file_name: pg.text,
    p_migration_file_name: pg.text
) RETURNS mgr_migration AS $$
DECLARE
    v_last_migration_id int8;
    v_generated_name text;
    v_current_date timestamptz;
    v_result mgr_migration;
    v_extension text := '.py';
BEGIN
    v_last_migration_id := currval('mgr_migration_id_seq') + 1;
    v_current_date := now() AT TIME ZONE 'UTC';
    IF p_with_datafix THEN
        v_extension := ''
    END IF;
    v_generated_name := format('migration_%s_%s%s', v_last_migration_id, to_char(v_current_date, 'YYYYMMDD'), v_extension);
    INSERT INTO mgr_migration(with_datafix, generated_name, created_at)
    VALUES (p_with_datafix, v_generated_name, v_current_date)
    RETURNING * INTO v_result;
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION mgr_get_last_executed_migration_revision()
RETURNS int8 AS $$
BEGIN
    RETURN currval('mgr_migration_id_seq');
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION mgr_get_last_generated_migration_revision()
RETURNS int8 AS $$
BEGIN
    RETURN currval('mgr_migration_revision_seq');
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION mgr_get_migrations_in_range(
    p_from int8,
    p_to int8
) RETURNS SETOF mgr_migration AS $$
BEGIN
    RETURN QUERY 
        SELECT * FROM mgr_migration
        WHERE id > p_from and id < p_to
    ;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION mgr_register_execution(
    p_migration mgr_migration,
    p_type mgr_migration_execution_type,
    p_comment text
) RETURNS void AS $$
BEGIN
    INSERT INTO mgr_migration_execution(migration_id, executed_at, type, comment)
    VALUES (p_migration.id, now() AT TIME ZONE 'UTC', p_type, p_comment);
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION mgr_get_migration_by_id(
    p_id int8
) RETURNS mgr_migration AS $$
DECLARE
    v_result mgr_migration;
BEGIN
    SELECT * FROM mgr_migration
    INTO v_result
    WHERE id = p_id;
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
