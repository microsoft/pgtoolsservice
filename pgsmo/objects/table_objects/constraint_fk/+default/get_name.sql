{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT conname as name
FROM pg_catalog.pg_constraint ct
WHERE ct.oid = {{fkid}}::oid
