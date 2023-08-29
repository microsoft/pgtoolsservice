{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% set enable_map = {'R':'ENABLE REPLICA', 'A':'ENABLE ALWAYS', 'O':'ENABLE', 'D':'DISABLE'} %}
ALTER TABLE {{ conn|qtIdent(data.schema, data.table) }}
    {{ enable_map[data.is_enable_trigger] }} TRIGGER {{ conn|qtIdent(data.name) }};
