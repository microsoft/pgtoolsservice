{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{#============================Create new view=========================#}
{% if display_comments %}
-- View: {{ conn|qtIdent(data.schema, data.name) }}

-- DROP VIEW {{ conn|qtIdent(data.schema, data.name) }};

{% endif %}
{% if data.name and data.schema and data.definition %}
CREATE OR REPLACE VIEW {{ conn|qtIdent(data.schema, data.name) }} AS
{{ data.definition.rstrip(';') }};
{% if data.owner %}

ALTER TABLE {{ conn|qtIdent(data.schema, data.name) }}
    OWNER TO {{ conn|qtIdent(data.owner) }};
{% endif %}
{% if data.comment %}
COMMENT ON VIEW {{ conn|qtIdent(data.schema, data.name) }}
    IS {{ data.comment }};
{% endif %}
{% endif %}
