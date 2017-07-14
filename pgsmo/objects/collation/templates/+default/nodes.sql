{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT c.oid, c.collname AS name
FROM pg_collation c
{% if parent_id %}
WHERE c.collnamespace = {{parent_id}}::oid
{% elif coid %}
WHERE c.oid = {{coid}}::oid
{% endif %}
ORDER BY c.collname;
