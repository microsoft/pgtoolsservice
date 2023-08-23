{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT opcname
FROM pg_catalog.pg_opclass opc,
pg_catalog.pg_am am
WHERE opcmethod=am.oid AND
      am.amname ={{indextype|qtLiteral(conn)}} AND
      NOT opcdefault
ORDER BY 1
