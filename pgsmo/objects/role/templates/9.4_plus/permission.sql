{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT
    rolname, rolcanlogin, rolsuper AS rolcatupdate, rolsuper
FROM
    pg_roles
WHERE oid = {{ rid }}::OID
