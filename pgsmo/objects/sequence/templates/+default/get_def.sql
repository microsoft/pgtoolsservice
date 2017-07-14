{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT
    last_value, 
    min_value, 
    max_value,
    start_value,
    cache_value,
    is_cycled, 
    increment_by,
    is_called
FROM {{ conn|qtIdent(data.schema) }}.{{ conn|qtIdent(data.name) }}