{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT
    pr.oid, pr.proname || '(' || COALESCE(pg_catalog
    .pg_get_function_identity_arguments(pr.oid), '') || ')' as name,
    lanname, pg_catalog.pg_get_userbyid(proowner) as funcowner, pr.pronamespace AS nsp
FROM
    pg_catalog.pg_proc pr
JOIN
    pg_catalog.pg_type typ ON typ.oid=prorettype
JOIN
    pg_catalog.pg_language lng ON lng.oid=prolang
JOIN
    pg_catalog.pg_namespace nsp ON nsp.oid=pr.pronamespace
    AND nsp.nspname={{ nspname }}
WHERE
    pr.prokind = 'p'::char
    AND typname NOT IN ('trigger', 'event_trigger')
    AND pr.proname = {{ name }};
    