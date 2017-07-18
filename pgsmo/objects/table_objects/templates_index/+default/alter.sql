{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{## Alter index to use cluster type ##}
{% if data.indisclustered %}

ALTER TABLE {{conn|qtIdent(data.schema, data.table)}}
    CLUSTER ON {{conn|qtIdent(data.name)}};
{% endif %}
{## Changes description ##}
{% if data.description is defined and data.description %}

COMMENT ON INDEX {{conn|qtIdent(data.schema, data.name)}}
    IS {{data.description|qtLiteral}};{% endif %}