{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT c.oid, c.collname AS name, c.collcollate AS lc_collate, c.collctype AS lc_type,
    pg_get_userbyid(c.collowner) AS owner, description, n.nspname AS schema
FROM pg_collation c
    JOIN pg_namespace n ON n.oid=c.collnamespace
    LEFT OUTER JOIN pg_description des ON (des.objoid=c.oid AND des.classoid='pg_collation'::regclass)
 
{% if coid %}    WHERE c.oid = {{coid}}::oid {% endif %}
ORDER BY c.collname;
