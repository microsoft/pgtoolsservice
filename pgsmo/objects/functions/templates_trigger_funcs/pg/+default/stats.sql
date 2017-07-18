{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT
    calls AS {{ conn|qtIdent(_('Number of calls')) }},
    total_time AS {{ conn|qtIdent(_('Total time')) }},
    self_time AS {{ conn|qtIdent(_('Self time')) }}
FROM
    pg_stat_user_functions
WHERE
    funcid = {{fnid}}::OID
