SELECT c.oid, c.collname AS name
FROM pg_collation c
{% if parent_id %}
WHERE c.collnamespace = {{parent_id}}::oid
{% elif coid %}
WHERE c.oid = {{coid}}::oid
{% endif %}
ORDER BY c.collname;
