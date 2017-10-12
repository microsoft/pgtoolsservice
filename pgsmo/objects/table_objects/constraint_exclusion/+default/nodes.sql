{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT conindid as oid,
    conname as name,
    NOT convalidated as convalidated
FROM pg_constraint ct
WHERE contype='x' AND
    conrelid = {{parent_id}}::oid
{% if exid %}
    AND conindid = {{exid}}::oid
{% endif %}
ORDER BY conname