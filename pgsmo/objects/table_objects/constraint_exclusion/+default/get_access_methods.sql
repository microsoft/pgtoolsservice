{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT amname
FROM pg_catalog.pg_am
WHERE EXISTS (SELECT 1
              FROM pg_catalog.pg_proc
              WHERE oid=amhandler)
ORDER BY amname;
