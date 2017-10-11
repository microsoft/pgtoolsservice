{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% import 'systemobjects.macros' as SYSOBJECTS %}

SELECT
    rel.oid,
    rel.relname AS name,
    nsp.nspname AS schema,
    nsp.oid AS schemaoid,
    {{ SYSOBJECTS.IS_SYSTEMSCHEMA('nsp') }} as is_system
FROM pg_class rel
INNER JOIN pg_namespace nsp ON rel.relnamespace= nsp.oid
WHERE
      rel.relkind = 'm'
    {% if (vid and datlastsysoid) %}
        AND c.oid = {{vid}}::oid
    {% endif %}
ORDER BY nsp.nspname, rel.relname
