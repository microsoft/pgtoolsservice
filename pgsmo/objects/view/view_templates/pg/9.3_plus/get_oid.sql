{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{# ===== fetch new assigned schema id ===== #}
{% if vid %}
SELECT
    c.relnamespace as scid
FROM
    pg_class c
WHERE
    c.oid = {{vid}}::oid;
{% endif %}
