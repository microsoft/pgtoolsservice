{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT
    pg_catalog.pg_get_functiondef({{fnid}}::oid) AS func_def,
    COALESCE(pg_catalog.pg_get_function_identity_arguments(pr.oid), '') as
    func_with_identity_arguments,
    nspname,
    pr.proname as proname,
    COALESCE(pg_catalog.pg_get_function_arguments(pr.oid), '') as func_args
FROM
    pg_catalog.pg_proc pr
JOIN
    pg_catalog.pg_namespace nsp ON nsp.oid=pr.pronamespace
WHERE
    pr.prokind = 'p'::char
    AND pronamespace = {{scid}}::oid
    AND pr.oid = {{fnid}}::oid;