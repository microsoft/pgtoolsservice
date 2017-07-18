{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT concat(quote_ident(nspname), '.', quote_ident(collname))  AS name
FROM pg_collation c, pg_namespace n
WHERE c.collnamespace = n.oid AND
    n.oid = {{ scid }}::oid AND
    c.oid = {{ coid }}::oid;
