

-- DATAFIX_ID: {datafix_id}
-- NOTE:      These functions are designed to reside in the extension
--            namespace as all other migration types/functions. They will
--            be executed before the up and down method in the
--            migration.py file. They are required if the migration is
--            flagged as with_datafix.


CREATE OR REPLACE FUNCTION mgr_datafix_{datafix_id}_up()
RETURNS int8 AS $$
BEGIN
    -- your code here

END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION mgr_datafix_{datafix_id}_down()
RETURNS void AS $$
BEGIN
    -- your code here

END;
$$ LANGUAGE plpgsql;
