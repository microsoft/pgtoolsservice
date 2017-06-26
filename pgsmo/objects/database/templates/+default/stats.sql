{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT
    {% if not did %}db.datname AS {{ conn|qtIdent(_('Database')) }}, {% endif %}
    numbackends AS {{ conn|qtIdent(_('Backends')) }},
    xact_commit AS {{ conn|qtIdent(_('Xact committed')) }},
    xact_rollback AS {{ conn|qtIdent(_('Xact rolled back')) }},
    blks_read AS {{ conn|qtIdent(_('Blocks read')) }},
    blks_hit AS {{ conn|qtIdent(_('Blocks hit')) }},
    tup_returned AS {{ conn|qtIdent(_('Tuples returned')) }},
    tup_fetched AS {{ conn|qtIdent(_('Tuples fetched')) }},
    tup_inserted AS {{ conn|qtIdent(_('Tuples inserted')) }},
    tup_updated AS {{ conn|qtIdent(_('Tuples updated')) }},
    tup_deleted AS {{ conn|qtIdent(_('Tuples deleted')) }},
    stats_reset AS {{ conn|qtIdent(_('Last statistics reset')) }},
    slave.confl_tablespace AS {{ conn|qtIdent(_('Tablespace conflicts')) }},
    slave.confl_lock AS {{ conn|qtIdent(_('Lock conflicts')) }},
    slave.confl_snapshot AS {{ conn|qtIdent(_('Snapshot conflicts')) }},
    slave.confl_bufferpin AS {{ conn|qtIdent(_('Bufferpin conflicts')) }},
    slave.confl_deadlock AS {{ conn|qtIdent(_('Deadlock conflicts')) }},
    pg_database_size(db.datid) AS {{ conn|qtIdent(_('Size')) }}
FROM
    pg_stat_database db
    LEFT JOIN pg_stat_database_conflicts slave ON db.datid=slave.datid
WHERE {% if did %}
db.datid = {{ did|qtLiteral }}::OID{% else %}
db.datid > {{ last_system_oid|qtLiteral }}::OID
{% endif %}

ORDER BY db.datname;
