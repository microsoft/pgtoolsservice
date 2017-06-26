{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT
    name, vartype, min_val, max_val, enumvals
FROM pg_settings
WHERE context in ('user', 'superuser');
