{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{### SQL to update constraint object ###}
{% if data %}
{# ==== To update constraint name ==== #}
{% if data.name != o_data.name %}
ALTER TABLE {{ conn|qtIdent(data.schema, data.table) }}
    RENAME CONSTRAINT {{ conn|qtIdent(o_data.name) }} TO {{ conn|qtIdent(data.name) }};
{% endif %}
{# ==== To update constraint tablespace ==== #}
{% if data.spcname and data.spcname != o_data.spcname %}
ALTER INDEX {{ conn|qtIdent(data.schema, data.name) }}
    SET TABLESPACE {{ conn|qtIdent(data.spcname) }};
{% endif %}
{% if data.fillfactor and data.fillfactor != o_data.fillfactor %}
ALTER INDEX {{ conn|qtIdent(data.schema, data.name) }}
    SET (FILLFACTOR={{ data.fillfactor }});
{% endif %}
{# ==== To update constraint comments ==== #}
{% if data.comment is defined and data.comment != o_data.comment %}
COMMENT ON CONSTRAINT {{ conn|qtIdent(data.name) }} ON {{ conn|qtIdent(data.schema, data.table) }}
    IS {{ data.comment|qtLiteral }};
{% endif %}
{% endif %}