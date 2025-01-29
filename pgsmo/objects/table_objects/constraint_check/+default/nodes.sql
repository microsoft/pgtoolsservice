{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT c.oid, conname as name,
    NOT convalidated as convalidated, conislocal, description as comment
    FROM pg_catalog.pg_constraint c
LEFT OUTER JOIN
    pg_catalog.pg_description des ON (des.objoid=c.oid AND
                           des.classoid='pg_constraint'::regclass)
WHERE contype = 'c'
    AND conrelid = {{ parent_id }}::oid
{% if cid %}
    AND c.oid = {{ cid }}::oid
{% endif %}
