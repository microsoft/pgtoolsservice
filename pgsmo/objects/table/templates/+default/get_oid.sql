{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT rel.oid as tid
FROM pg_class rel
WHERE rel.relkind IN ('r','s','t')
AND rel.relnamespace = {{ scid }}::oid
AND rel.relname = {{data.name|qtLiteral}}