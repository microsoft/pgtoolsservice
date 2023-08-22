{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT
    pr.oid, pr.xmin, pr.proiswindow, pr.prosrc, pr.prosrc AS prosrc_c,
    pr.pronamespace, pr.prolang, pr.procost, pr.prorows,
    pr.prosecdef, pr.proleakproof, pr.proisstrict, pr.proretset, pr.provolatile,
    pr.pronargs, pr.prorettype, pr.proallargtypes, pr.proargmodes, pr.probin, pr.proacl,
    pr.proname, pr.proname AS name, pg_catalog.pg_get_function_result(pr.oid) AS prorettypename,
    typns.nspname AS typnsp, lanname, proargnames, pg_catalog.oidvectortypes(proargtypes) AS proargtypenames,
    pg_catalog.pg_get_expr(proargdefaults, 'pg_catalog.pg_class'::regclass) AS proargdefaultvals,
    pronargdefaults, proconfig, pg_catalog.pg_get_userbyid(proowner) AS funcowner, description,
    (SELECT
        pg_catalog.array_agg(provider || '=' || label)
    FROM
        pg_catalog.pg_seclabel sl1
    WHERE
        sl1.objoid=pr.oid) AS seclabels
FROM
    pg_catalog.pg_proc pr
JOIN
    pg_catalog.pg_type typ ON typ.oid=prorettype
JOIN
    pg_catalog.pg_namespace typns ON typns.oid=typ.typnamespace
JOIN
    pg_catalog.pg_language lng ON lng.oid=prolang
LEFT OUTER JOIN
    pg_catalog.pg_description des ON (des.objoid=pr.oid AND des.classoid='pg_proc'::regclass and des.objsubid = 0)
WHERE
    proisagg = FALSE
    AND typname IN ('trigger', 'event_trigger')
    AND lanname NOT IN ('edbspl', 'sql', 'internal')
{% if fnid %}
    AND pr.oid = {{fnid}}::oid
{% else %}
    AND pronamespace = {{scid}}::oid
{% endif %}
ORDER BY
    proname;
