{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT
    pr.oid, pr.proname || '(' || COALESCE(pg_catalog.pg_get_function_identity_arguments(pr.oid), '') || ')' AS name,
    lanname, pg_get_userbyid(proowner) AS funcowner, description
FROM
    pg_proc pr
JOIN
    pg_type typ ON typ.oid=prorettype
JOIN
    pg_language lng ON lng.oid=prolang
LEFT OUTER JOIN
    pg_description des ON (des.objoid=pr.oid AND des.classoid='pg_proc'::regclass)
WHERE
    proisagg = FALSE
    AND pr.protype = '0'::char
{% if fnid %}
    AND pr.oid = {{ fnid|qtLiteral }}
{% endif %}
{% if parent_id %}
    AND pronamespace = {{parent_id}}::oid
{% endif %}
    AND typname NOT IN ('trigger', 'event_trigger')
ORDER BY
    proname;
