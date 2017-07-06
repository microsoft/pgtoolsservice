{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{### SQL to fetch tablespace object properties ###}
SELECT
    ts.oid, spcname AS name, spclocation, spcoptions,
    pg_get_userbyid(spcowner) as spcuser,
    pg_catalog.shobj_description(oid, 'pg_tablespace') AS description,
    array_to_string(spcacl::text[], ', ') as acl
FROM
    pg_tablespace ts
{% if tsid %}
WHERE ts.oid={{ tsid|qtLiteral }}::OID
{% endif %}
ORDER BY name
