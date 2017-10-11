{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{# ===== Below will provide view id for last created view ==== #}
{% if data %}
SELECT c.oid, c.relname FROM pg_class c WHERE c.relname = {{ data.name|qtLiteral }};
{% endif %}
