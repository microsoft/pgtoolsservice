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
