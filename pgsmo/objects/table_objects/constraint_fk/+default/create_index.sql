{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% if data.autoindex and data.coveringindex%}
CREATE INDEX IF NOT EXISTS {{ conn|qtIdent(data.coveringindex) }}
    ON {{ conn|qtIdent(data.schema, data.table) }}({% for columnobj in data.columns %}{% if loop.index != 1 %}
, {% endif %}{{ conn|qtIdent(columnobj.local_column)}}{% endfor %});
{% endif %}
