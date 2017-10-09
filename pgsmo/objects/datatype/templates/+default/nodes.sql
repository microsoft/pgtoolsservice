{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% import 'systemobjects.macros' as SYSOBJECTS %}
SELECT  t.oid,
		t.typname AS name, 
        nsp.nspname as schema,
        nsp.oid AS schemaoid,
        {{ SYSOBJECTS.IS_SYSTEMSCHEMA('nsp') }} as is_system
FROM pg_type t
    LEFT OUTER JOIN pg_type e ON e.oid=t.typelem
    LEFT OUTER JOIN pg_class ct ON ct.oid=t.typrelid AND ct.relkind <> 'c'
    LEFT OUTER JOIN pg_namespace nsp ON nsp.oid = t.typnamespace
WHERE t.typtype != 'd' AND t.typname NOT LIKE E'\\_%' 
{% if tid %}
    AND t.oid = {{tid}}::oid
{% endif %}
{% if not show_system_objects %}
    AND ct.oid is NULL
{% endif %}
ORDER BY t.typname;