{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{# We need database name before we execute drop #}
{% if did %}
SELECT db.datname as name FROM pg_database as db WHERE db.oid = {{did}};
{% endif %}
{# Using name from above query we will drop the database #}
{% if datname %}
DROP DATABASE {{ conn|qtIdent(datname) }};
{% endif %}
