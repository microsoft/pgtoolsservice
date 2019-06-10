{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% import 'systemobjects.macros' as SYSOBJECTS %} 
SELECT
    pr.oid, 
    pr.proname || '(' || COALESCE(pg_catalog.pg_get_function_identity_arguments(pr.oid), '') || ')' as name,
    lanname, pg_get_userbyid(proowner) as funcowner, 
    description,
    nsp.nspname AS schema,
    nsp.oid AS schemaoid,
    {{ SYSOBJECTS.IS_SYSTEMSCHEMA('nsp') }} as is_system
FROM
    pg_proc pr
JOIN 
    pg_namespace nsp ON pr.pronamespace= nsp.oid
JOIN
    pg_type typ ON typ.oid=prorettype
JOIN
    pg_language lng ON lng.oid=prolang
LEFT OUTER JOIN
    pg_description des ON (des.objoid=pr.oid AND des.classoid='pg_proc'::regclass)
WHERE
   pr.prokind IN ('f', 'w')
{% if fnid %}
    AND pr.oid = {{ fnid|qtLiteral }}
{% endif %}
{% if scid %}
    AND pronamespace = {{scid}}::oid
{% endif %}
    AND typname NOT IN ('trigger', 'event_trigger')
ORDER BY
    proname;
