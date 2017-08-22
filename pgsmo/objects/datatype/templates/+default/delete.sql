{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
DROP TYPE {{ conn|qtIdent(data.schema, data.name) }}{% if cascade%} CASCADE{% endif %};