{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT cls.relname, cls.oid
FROM pg_catalog.pg_index idx
    JOIN pg_catalog.pg_class cls ON cls.oid=indexrelid
WHERE indrelid = {{tid}}::OID
ORDER BY cls.oid DESC LIMIT 1;
