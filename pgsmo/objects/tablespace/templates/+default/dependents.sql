{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% if fetch_database %}
SELECT datname,
    datallowconn AND pg_catalog.has_database_privilege(datname, 'CONNECT') AS datallowconn,
    dattablespace
FROM pg_database db
ORDER BY datname
{% endif %}

{% if fetch_dependents %}
SELECT cl.relkind, COALESCE(cin.nspname, cln.nspname) as nspname,
    COALESCE(ci.relname, cl.relname) as relname, cl.relname as indname
FROM pg_class cl
JOIN pg_namespace cln ON cl.relnamespace=cln.oid
LEFT OUTER JOIN pg_index ind ON ind.indexrelid=cl.oid
LEFT OUTER JOIN pg_class ci ON ind.indrelid=ci.oid
LEFT OUTER JOIN pg_namespace cin ON ci.relnamespace=cin.oid,
pg_database WHERE datname = current_database() AND
(cl.reltablespace = {{tsid}}::oid OR (cl.reltablespace=0 AND dattablespace = {{tsid}}::oid))
ORDER BY 1,2,3
{% endif %}