{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT
    c.oid,
    c.relname AS name
FROM pg_class c
WHERE
  c.relkind = 'v'
{% if (vid and datlastsysoid) %}
    AND c.oid = {{vid}}::oid
{% elif parent_id %}
    AND c.relnamespace = {{parent_id}}::oid
ORDER BY
    c.relname
{% endif %}