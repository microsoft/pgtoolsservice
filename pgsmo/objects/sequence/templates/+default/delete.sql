{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
DROP SEQUENCE {{ conn|qtIdent(data.schema) }}.{{ conn|qtIdent(data.name) }}{% if cascade%} CASCADE{% endif %};
