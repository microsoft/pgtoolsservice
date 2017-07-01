{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{### SQL to fetch tablespace object stats ###}
{% if tsid %}
SELECT pg_tablespace_size({{ tsid|qtLiteral }}::OID) AS {{ conn|qtIdent(_('Size')) }}
{% else %}
SELECT ts.spcname AS {{ conn|qtIdent(_('Name')) }},
    pg_tablespace_size(ts.oid) AS {{ conn|qtIdent(_('Size')) }}
FROM
    pg_catalog.pg_tablespace ts;
{% endif %}
