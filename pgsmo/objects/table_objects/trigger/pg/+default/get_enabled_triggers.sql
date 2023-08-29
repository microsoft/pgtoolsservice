{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT count(*) FROM pg_catalog.pg_trigger WHERE tgrelid={{tid}} AND tgisinternal = FALSE AND tgenabled = 'O'
