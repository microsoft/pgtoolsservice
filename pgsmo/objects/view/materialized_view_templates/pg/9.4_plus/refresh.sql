{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{#= Refresh materialized view =#}
REFRESH MATERIALIZED VIEW{% if is_concurrent %} CONCURRENTLY{% endif %} {{ conn|qtIdent(nspname, name) }} WITH {% if not with_data %}NO {% endif %}DATA;
