{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT ct.oid,
    ct.conname as name,
    NOT convalidated as convalidated
FROM pg_catalog.pg_constraint ct
WHERE contype='c' AND
    conrelid = {{tid}}::oid
ORDER BY ct.oid DESC LIMIT 1;
