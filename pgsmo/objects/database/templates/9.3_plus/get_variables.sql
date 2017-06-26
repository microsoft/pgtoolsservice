{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT
    rl.*, r.rolname AS user_name, db.datname as db_name
FROM pg_db_role_setting AS rl
    LEFT JOIN pg_roles AS r ON rl.setrole = r.oid
    LEFT JOIN pg_database AS db ON rl.setdatabase = db.oid
WHERE setdatabase = {{did}}
