{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT DISTINCT ON(cls.relname) cls.oid
FROM pg_index idx
    JOIN pg_class cls ON cls.oid=indexrelid
    JOIN pg_class tab ON tab.oid=indrelid
    JOIN pg_namespace n ON n.oid=tab.relnamespace
WHERE indrelid = {{tid}}::OID
    AND cls.relname = {{data.name|qtLiteral}};