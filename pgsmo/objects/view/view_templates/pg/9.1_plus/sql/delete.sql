{# ====================== Drop/Cascade view by name ===================== #}
{% if vid %}
SELECT
    c.relname AS name,
    nsp.nspname
FROM
    pg_class c
LEFT JOIN pg_namespace nsp ON c.relnamespace = nsp.oid
WHERE
    c.relfilenode = {{ vid }};
{% elif (name and nspname) %}
DROP VIEW {{ conn|qtIdent(nspname, name) }} {% if cascade %} CASCADE {% endif %};
{% endif %}
