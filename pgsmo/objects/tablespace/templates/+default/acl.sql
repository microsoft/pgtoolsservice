{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{### SQL to fetch privileges for tablespace ###}
SELECT 'spcacl' as deftype, COALESCE(gt.rolname, 'PUBLIC') grantee, g.rolname grantor,
    array_agg(privilege_type) as privileges, array_agg(is_grantable) as grantable
FROM
  (SELECT
    d.grantee, d.grantor, d.is_grantable,
    CASE d.privilege_type
    WHEN 'CREATE' THEN 'C'
    ELSE 'UNKNOWN'
    END AS privilege_type
  FROM
    (SELECT ts.spcacl
        FROM pg_tablespace ts
        {% if tsid %}
        WHERE ts.oid={{ tsid|qtLiteral }}::OID
        {% endif %}
    ) acl,
    (SELECT (d).grantee AS grantee, (d).grantor AS grantor, (d).is_grantable
        AS is_grantable, (d).privilege_type AS privilege_type FROM (SELECT
        aclexplode(ts.spcacl) as d FROM pg_tablespace ts
        {% if tsid %}
        WHERE ts.oid={{ tsid|qtLiteral }}::OID
        {% endif %}
        ) a) d
    ) d
  LEFT JOIN pg_catalog.pg_roles g ON (d.grantor = g.oid)
  LEFT JOIN pg_catalog.pg_roles gt ON (d.grantee = gt.oid)
GROUP BY g.rolname, gt.rolname
