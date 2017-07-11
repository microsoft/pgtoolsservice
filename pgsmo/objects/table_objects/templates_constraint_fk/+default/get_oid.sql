{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT ct.oid,
    NOT convalidated as convalidated
FROM pg_constraint ct
WHERE contype='f' AND
ct.conname = {{ name|qtLiteral }};