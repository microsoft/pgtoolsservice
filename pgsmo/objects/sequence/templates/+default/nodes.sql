{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% import 'systemobjects.macros' as SYSOBJECTS %}
SELECT  rel.oid as oid, 
        rel.relname as name, 
        nsp.nspname as schema,
        nsp.oid AS schemaoid,
        {{ SYSOBJECTS.IS_SYSTEMSCHEMA('nsp') }} as is_system
FROM pg_class rel
INNER JOIN 
    pg_namespace nsp ON rel.relnamespace= nsp.oid
WHERE
    relkind = 'S'
{% if seid %}
    AND rel.oid = {{seid|qtLiteral}}::oid
{% endif %}
ORDER BY relname
