{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT conname as name,
    NOT convalidated as convalidated
FROM pg_catalog.pg_constraint ct
WHERE contype = 'c'
AND  ct.oid = {{cid}}::oid
