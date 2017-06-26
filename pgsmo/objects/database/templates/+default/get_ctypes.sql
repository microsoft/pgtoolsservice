{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT DISTINCT(datctype) AS cname
FROM pg_database
UNION
SELECT DISTINCT(datcollate) AS cname
FROM pg_database