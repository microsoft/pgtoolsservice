{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% import 'catalogs.sql' as CATALOGS %}
{% import 'systemobjects.macros' as SYSOBJECTS %}
SELECT
    nsp.oid,
    nsp.nspname as name,
    has_schema_privilege(nsp.oid, 'CREATE') as can_create,
    has_schema_privilege(nsp.oid, 'USAGE') as has_usage,
    {{ SYSOBJECTS.IS_SYSTEMSCHEMA('nsp') }} as is_system
FROM
    pg_namespace nsp
WHERE
    nsp.nspparent = 0 
    {% if scid %}
    AND nsp.oid={{scid}}::oid 
    {% endif %}
ORDER BY nspname;
