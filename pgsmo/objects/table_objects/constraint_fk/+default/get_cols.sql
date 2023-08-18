{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% for n in range(colcnt|int) %}
{% if loop.index != 1 %}
UNION SELECT  pg_catalog.pg_get_indexdef({{ cid|string }}, {{ loop.index|string }}, true) AS column
{% else %}
SELECT  pg_catalog.pg_get_indexdef({{ cid|string }} , {{ loop.index|string }} , true) AS column
{% endif %}
{% endfor %}
