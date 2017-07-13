{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT t.oid, t.tgname as name, (CASE WHEN tgenabled = 'O' THEN true ElSE false END) AS is_enable_trigger
FROM pg_trigger t
    WHERE tgrelid = {{parent_id}}::OID
{% if trid %}
    AND t.oid = {{trid}}::OID
{% endif %}
    ORDER BY tgname;
