{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
ALTER TABLE {{ conn|qtIdent(data.schema, data.name) }}
    {% if is_enable_trigger == True %}ENABLE{% else %}DISABLE{% endif %} TRIGGER ALL;