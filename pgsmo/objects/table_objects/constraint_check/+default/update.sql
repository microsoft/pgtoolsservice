{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% if data.comment is defined and data.comment != o_data.comment %}
COMMENT ON CONSTRAINT {{ conn|qtIdent(o_data.name) }} ON {{ conn|qtIdent(o_data.nspname, o_data.relname) }}
    IS {{ data.comment|qtLiteral }};
{% endif %}