{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT opcname,  opcmethod
FROM pg_opclass
    WHERE opcmethod = {{oid}}::OID
    AND NOT opcdefault
    ORDER BY 1;