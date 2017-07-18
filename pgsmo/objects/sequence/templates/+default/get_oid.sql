{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT cl.oid as oid, relnamespace
FROM pg_class cl
LEFT OUTER JOIN pg_description des ON (des.objoid=cl.oid AND des.classoid='pg_class'::regclass)
LEFT OUTER JOIN pg_namespace nsp ON (nsp.oid = cl.relnamespace)
WHERE relkind = 'S'
AND relname = {{ name|qtLiteral }}
AND nspname = {{ schema|qtLiteral }}
