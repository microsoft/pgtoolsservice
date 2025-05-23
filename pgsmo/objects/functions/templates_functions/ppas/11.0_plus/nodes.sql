{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% import 'systemobjects.macros' as SYSOBJECTS %} 
SELECT
    pr.oid,
    pr.proname || '(' || COALESCE(pg_catalog.pg_get_function_identity_arguments(pr.oid), '') || ')' AS name,
    lanname,
    pg_catalog.pg_get_userbyid(proowner) AS funcowner,
    description,
    nsp.nspname AS schema,
    nsp.oid AS schemaoid,
    {{ SYSOBJECTS.IS_SYSTEMSCHEMA('nsp') }} AS is_system
FROM
    pg_catalog.pg_proc pr
INNER JOIN
    pg_catalog.pg_namespace nsp ON pr.pronamespace = nsp.oid
JOIN
    pg_catalog.pg_type typ ON typ.oid=prorettype
JOIN
    pg_catalog.pg_language lng ON lng.oid=prolang
LEFT OUTER JOIN
    pg_catalog.pg_description des ON (des.objoid=pr.oid AND des.classoid='pg_proc'::regclass)
WHERE
    pr.prokind IN ('f', 'w')
    AND pr.protype = '0'::char
{% if fnid %}
    AND pr.oid = {{ fnid|qtLiteral(conn) }}
{% endif %}
{% if scid %}
    AND pronamespace = {{scid}}::oid
{% endif %}
{% if schema_diff %}
    AND CASE WHEN (SELECT COUNT(*) FROM pg_catalog.pg_depend
        WHERE objid = pr.oid AND deptype = 'e') > 0 THEN FALSE ELSE TRUE END
{% endif %}
    AND typname NOT IN ('trigger', 'event_trigger')
ORDER BY
    proname;
