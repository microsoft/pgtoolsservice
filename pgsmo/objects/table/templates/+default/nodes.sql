{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% import 'systemobjects.macros' as SYSOBJECTS %}
SELECT  rel.oid,
        (SELECT count(*) FROM pg_trigger WHERE tgrelid=rel.oid) AS triggercount,
        (SELECT count(*) FROM pg_trigger WHERE tgrelid=rel.oid AND tgenabled = 'O') AS has_enable_triggers,
        (CASE WHEN rel.relkind = 'p' THEN true ELSE false END) AS is_partitioned,
        nsp.nspname AS schema,
        nsp.oid AS schemaoid,
        rel.relname AS name,
        {{ SYSOBJECTS.IS_SYSTEMSCHEMA('nsp') }} as is_system
FROM pg_class rel
INNER JOIN pg_namespace nsp ON rel.relnamespace= nsp.oid
    WHERE rel.relkind IN ('r','t','f','p')
     {% if tid %} AND rel.oid = {{tid}}::OID {% endif %}
    AND NOT rel.relispartition
    ORDER BY nsp.nspname, rel.relname;
