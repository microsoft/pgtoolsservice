{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{# ===== get view name against view id ==== #}
{% if vid %}
SELECT
    c.relname AS name,
    nsp.nspname AS schema
FROM
    pg_class c
    LEFT OUTER JOIN pg_namespace nsp on nsp.oid = c.relnamespace
WHERE
    c.oid = {{vid}}
{% endif %}
