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
       {# The first normal object id is given in PG source code. Article here describes it: https://dba.stackexchange.com/questions/316723/oid-release-ranges-for-built-in-aka-standard-database-objects-during-postgresq
       # We set datlastsysoid to one less than that for PG 15 and above because the datlastsysoid column no longer is present past that
       #}
       16383 as datlastsysoid,
       has_database_privilege(db.oid, 'CREATE') as cancreate, 
       datdba as owner, 
       db.datistemplate , 
       has_database_privilege(db.datname, 'connect') as canconnect,
       datistemplate as is_system
   
   FROM
       pg_database db
       LEFT OUTER JOIN pg_tablespace ta ON db.dattablespace = ta.oid
   {% if did %}
   WHERE db.oid = {{ did }}::OID
   {% elif last_system_oid %}
   WHERE db.oid > {{ last_system_oid }}::OID
   {% endif %}
   
   ORDER BY datname;
   