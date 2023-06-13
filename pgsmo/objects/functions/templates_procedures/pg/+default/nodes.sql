{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% import 'systemobjects.macros' as SYSOBJECTS %} 
SELECT
    pr.oid,
    CASE WHEN
        pg_catalog.pg_get_function_identity_arguments(pr.oid) <> ''
    THEN
        pr.proname || '(' || pg_catalog.pg_get_function_identity_arguments(pr.oid) || ')'
    ELSE
        pr.proname::text
    END AS name,
    lanname, pg_catalog.pg_get_userbyid(proowner) AS funcowner, description,
    nsp.nspname AS schema,
    nsp.oid AS schemaoid,
    {{ SYSOBJECTS.IS_SYSTEMSCHEMA('nsp') }} as is_system
FROM
    pg_proc pr
INNER JOIN 
    pg_namespace nsp ON pr.pronamespace= nsp.oid
JOIN
    pg_type typ ON typ.oid=prorettype
JOIN
    pg_language lng ON lng.oid=prolang
LEFT OUTER JOIN
    pg_description des ON (des.objoid=pr.oid AND des.classoid='pg_proc'::regclass)
WHERE
    pr.prokind = 'p'::char
{% if fnid %}
    AND pr.oid = {{ fnid }}
{% endif %}
{% if scid %}
    AND pr.pronamespace = {{scid}}::oid
{% endif %}
{% if schema_diff %}
    AND CASE WHEN (SELECT COUNT(*) FROM pg_catalog.pg_depend
        WHERE objid = pr.oid AND deptype = 'e') > 0 THEN FALSE ELSE TRUE END
{% endif %}
    AND typname NOT IN ('trigger', 'event_trigger')
ORDER BY
    proname;

