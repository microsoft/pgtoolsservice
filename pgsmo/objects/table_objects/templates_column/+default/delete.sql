{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
ALTER TABLE {{conn|qtIdent(data.schema, data.table)}} DROP COLUMN {{conn|qtIdent(data.name)}};