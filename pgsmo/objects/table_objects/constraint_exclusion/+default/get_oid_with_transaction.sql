{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT ct.conindid AS oid,
    ct.conname AS name,
    NOT convalidated AS convalidated
FROM pg_catalog.pg_constraint ct
WHERE contype='x' AND
    conrelid = {{tid}}::oid
ORDER BY oid DESC LIMIT 1;
