{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT
    split_part(rolconfig, '=', 1) AS name, replace(rolconfig, split_part(rolconfig, '=', 1) || '=', '') AS value, NULL::text AS database
FROM
    (SELECT
            unnest(rolconfig) AS rolconfig, rolcanlogin, rolname
    FROM
        pg_catalog.pg_roles
    WHERE
        oid={{ rid|qtLiteral }}::OID
    ) r

UNION ALL
SELECT
    split_part(rolconfig, '=', 1) AS name, replace(rolconfig, split_part(rolconfig, '=', 1) || '=', '') AS value, datname AS database
FROM
    (SELECT
        d.datname, unnest(c.setconfig) AS rolconfig
    FROM
        (SELECT *
        FROM pg_catalog.pg_db_role_setting dr
        WHERE
            dr.setrole={{ rid|qtLiteral }}::OID AND dr.setdatabase!=0
        ) c
        LEFT JOIN pg_catalog.pg_database d ON (d.oid = c.setdatabase)
    ) a;
