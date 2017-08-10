{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% import 'catalogs.sql' as CATALOGS %}
SELECT
    CASE
    WHEN (nspname LIKE E'pg\\_temp\\_%') THEN 1
    WHEN (nspname LIKE E'pg\\_%') THEN 0
    ELSE 3 END AS nsptyp,
    nsp.nspname AS name,
    nsp.oid,
    array_to_string(nsp.nspacl::text[], ', ') as acl,
    r.rolname AS namespaceowner, description,
    has_schema_privilege(nsp.oid, 'CREATE') AS can_create,
    CASE
    WHEN nspname LIKE E'pg\\_%' THEN true
    ELSE false END AS is_sys_object,
    {### Default ACL for Tables ###}
    (SELECT array_to_string(ARRAY(
        SELECT array_to_string(defaclacl::text[], ', ')
            FROM pg_default_acl
        WHERE defaclobjtype = 'r' AND defaclnamespace = nsp.oid
    ), ', ')) AS tblacl,
    {### Default ACL for Sequnces ###}
    (SELECT array_to_string(ARRAY(
        SELECT array_to_string(defaclacl::text[], ', ')
            FROM pg_default_acl
        WHERE defaclobjtype = 'S' AND defaclnamespace = nsp.oid
    ), ', ')) AS seqacl,
    {### Default ACL for Functions ###}
    (SELECT array_to_string(ARRAY(
        SELECT array_to_string(defaclacl::text[], ', ')
            FROM pg_default_acl
        WHERE defaclobjtype = 'f' AND defaclnamespace = nsp.oid
    ), ', ')) AS funcacl
FROM
    pg_namespace nsp
    LEFT OUTER JOIN pg_description des ON
        (des.objoid=nsp.oid AND des.classoid='pg_namespace'::regclass)
    LEFT JOIN pg_roles r ON (r.oid = nsp.nspowner)
WHERE
    {% if scid %}
    nsp.oid={{scid}}::oid AND
    {% else %}
    {% if show_sysobj %}
    nspname NOT LIKE E'pg\\_temp\\_%' AND
    nspname NOT LIKE E'pg\\_toast\\_temp\\_%' AND
    {% endif %}
    {% endif %}
    nsp.nspparent = 0 AND
    NOT (
{{ CATALOGS.LIST('nsp') }}
    )
ORDER BY 1, nspname;
