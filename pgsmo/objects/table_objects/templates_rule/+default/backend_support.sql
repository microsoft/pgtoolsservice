{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{#=============Checks if it is materialized view========#}
{% if vid %}
SELECT
    CASE WHEN c.relkind = 'm' THEN False ELSE True END As m_view
FROM
    pg_class c
WHERE
    c.oid = {{ vid }}::oid
{% endif %}
