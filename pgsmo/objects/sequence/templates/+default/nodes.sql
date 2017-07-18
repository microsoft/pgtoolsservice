{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT cl.oid as oid, relname as name, relnamespace as schema
FROM pg_class cl
WHERE
    relkind = 'S'
{% if parent_id %}
    AND relnamespace = {{parent_id|qtLiteral}}::oid
{% endif %}
{% if seid %}
    AND cl.oid = {{seid|qtLiteral}}::oid
{% endif %}
ORDER BY relname
