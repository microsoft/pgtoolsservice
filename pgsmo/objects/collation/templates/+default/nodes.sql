{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% import 'systemobjects.macros' as SYSOBJECTS %}
SELECT  c.oid, 
        c.collname AS name,
        nsp.nspname AS schema,
        nsp.oid AS schemaoid,
        {{ SYSOBJECTS.IS_SYSTEMSCHEMA('nsp') }} as is_system
FROM pg_collation c 
INNER JOIN 
    pg_namespace nsp ON c.collnamespace= nsp.oid
{% if coid %}
WHERE c.oid = {{coid}}::oid
{% endif %}
ORDER BY c.collname;
