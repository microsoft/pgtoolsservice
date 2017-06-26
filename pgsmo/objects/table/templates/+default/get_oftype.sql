{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% import 'table/sql/macros/db_catalogs.macro' as CATALOG %}
SELECT c.oid,
  quote_ident(n.nspname)||'.'||quote_ident(c.relname) AS typname
  FROM pg_namespace n, pg_class c
WHERE c.relkind = 'c' AND c.relnamespace=n.oid
{% if not show_system_objects %}
{{ CATALOG.VALID_CATALOGS(server_type) }}
{% endif %}
ORDER BY typname;