{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{# ============Create Rule============= #}
{% if display_comments %}
-- Rule: {{ conn|qtIdent(data.name) }} ON {{ conn|qtIdent(data.schema, data.view) }}

-- DROP Rule {{ conn|qtIdent(data.name) }} ON {{ conn|qtIdent(data.schema, data.view) }};

{% endif %}
{% if data.name and data.schema and data.view %}
CREATE OR REPLACE RULE {{ conn|qtIdent(data.name) }} AS
    ON {{ data.event|upper if data.event else 'SELECT' }} TO {{ conn|qtIdent(data.schema, data.view) }}
{% if data.condition %}
    WHERE {{ data.condition }}
{% endif %}
    DO{% if data.do_instead in ['true', True] %}
{{ ' INSTEAD' }}
{% else %}
{{ '' }}
{% endif %}
{% if data.statements %}
{{ data.statements.rstrip(';') }};
{% else %}
  NOTHING;
{% endif %}
{% if data.comment %}

COMMENT ON RULE {{ conn|qtIdent(data.name) }} ON {{ conn|qtIdent(data.schema, data.view) }} IS {{ data.comment|qtLiteral }};{% endif %}
{% endif %}
