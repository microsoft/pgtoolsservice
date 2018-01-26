{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT
    db.oid as oid, 
    db.datname as name, 
    ta.spcname as spcname, 
    db.datallowconn,
    db.datlastsysoid,
    has_database_privilege(db.oid, 'CREATE') as cancreate, 
    datdba as owner, 
    db.datistemplate , 
    has_database_privilege(db.datname, 'connect') as canconnect,
    datistemplate as is_system

FROM
    pg_database db
    LEFT OUTER JOIN pg_tablespace ta ON db.dattablespace = ta.oid
{% if did %}
WHERE db.oid = {{ did|qtLiteral }}::OID
{% elif last_system_oid %}
WHERE db.oid > {{ last_system_oid }}::OID
{% endif %}

ORDER BY datname;
