{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT
    oid, conname as name
FROM
    pg_constraint
WHERE
    conrelid = {{tid}}::oid
    AND conname={{ name|qtLiteral }};
