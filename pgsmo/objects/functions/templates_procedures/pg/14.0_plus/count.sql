{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT COUNT(*)
FROM
    pg_catalog.pg_proc pr
JOIN
    pg_catalog.pg_type typ ON typ.oid=prorettype
JOIN
    pg_catalog.pg_namespace typns ON typns.oid=typ.typnamespace
JOIN
    pg_catalog.pg_language lng ON lng.oid=prolang
WHERE
    pr.prokind = 'p'
    AND typname NOT IN ('trigger', 'event_trigger')
    AND pronamespace = {{scid}}::oid;