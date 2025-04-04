{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT
    funcname AS {{ conn|qtIdent(_('Name')) }},
    calls AS {{ conn|qtIdent(_('Number of calls')) }},
    total_time AS {{ conn|qtIdent(_('Total time')) }},
    self_time AS {{ conn|qtIdent(_('Self time')) }}
FROM
    pg_catalog.pg_stat_user_functions
WHERE
    schemaname = {{schema_name|qtLiteral(conn)}}
    AND funcid IN (
        SELECT p.oid
        FROM
            pg_catalog.pg_proc p
        JOIN
            pg_catalog.pg_type typ ON typ.oid=p.prorettype
        WHERE
            p.proisagg = FALSE
            AND typname = 'trigger'
    )
ORDER BY funcname;
