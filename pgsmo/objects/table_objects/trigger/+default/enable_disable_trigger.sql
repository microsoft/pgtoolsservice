{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
ALTER TABLE {{ conn|qtIdent(data.schema, data.table) }}
    {% if data.is_enable_trigger == True %}ENABLE{% else %}DISABLE{% endif %} TRIGGER {{ conn|qtIdent(data.name) }};