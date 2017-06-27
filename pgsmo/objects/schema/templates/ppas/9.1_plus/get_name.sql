{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT nsp.nspname FROM pg_namespace nsp WHERE nsp.oid = {{ scid|qtLiteral }};
