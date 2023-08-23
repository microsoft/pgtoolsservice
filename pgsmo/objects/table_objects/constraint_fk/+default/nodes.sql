{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT ct.oid,
    conname as name,
    NOT convalidated as convalidated,
    description as comment
FROM pg_catalog.pg_constraint ct
LEFT OUTER JOIN pg_catalog.pg_description des ON (des.objoid=ct.oid AND des.classoid='pg_constraint'::regclass)
WHERE contype='f' AND
    conrelid = {{parent_id}}::oid
ORDER BY conname
