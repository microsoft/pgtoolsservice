{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT --nspname, collname,
	CASE WHEN length(nspname::text) > 0 AND length(collname::text) > 0  THEN
	  pg_catalog.concat(quote_ident(nspname), '.', pg_catalog.quote_ident(collname))
	ELSE '' END AS collation
FROM pg_catalog.pg_collation c, pg_catalog.pg_namespace n
    WHERE c.collnamespace=n.oid
    ORDER BY nspname, collname;
