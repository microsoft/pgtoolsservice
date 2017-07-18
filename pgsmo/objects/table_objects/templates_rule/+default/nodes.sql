{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT
    rw.oid AS oid,
    rw.rulename AS name
FROM
    pg_rewrite rw
WHERE
{% if parent_id %}
    rw.ev_class = {{ parent_id }}
{% elif rid %}
    rw.oid = {{ rid }}
{% endif %}
ORDER BY
    rw.rulename
