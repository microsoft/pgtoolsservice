{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT
    format_type(oid, NULL) AS out_arg_type
FROM
    pg_type
WHERE
    oid = {{ out_arg_oid }}::oid;
