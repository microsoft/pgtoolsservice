{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
 
 SELECT
    attname as name, attnum as OID, typ.oid AS typoid, typ.typname AS datatype, attnotnull as not_null, attr.atthasdef as has_default_val
     ,nspname, relname, attrelid, 
     CASE WHEN typ.typtype = 'd' THEN typ.typtypmod ELSE atttypmod END AS typmod,
     CASE WHEN atthasdef THEN (SELECT pg_get_expr(adbin, cls.oid) FROM pg_attrdef WHERE adrelid = cls.oid AND adnum = attr.attnum) ELSE NULL END AS default,
     CASE WHEN col.is_updatable = 'YES' THEN true ELSE false END AS is_updatable,
     EXISTS (
       SELECT * FROM pg_index
       WHERE pg_index.indrelid = cls.oid AND
             pg_index.indisprimary AND
             attnum = ANY (indkey)
     ) AS isprimarykey,
     EXISTS (
       SELECT * FROM pg_index
       WHERE pg_index.indrelid = cls.oid AND
             pg_index.indisunique AND
             attnum = ANY (indkey)
     ) AS isunique
FROM pg_attribute AS attr
JOIN pg_type AS typ ON attr.atttypid = typ.oid
JOIN pg_class AS cls ON cls.oid = attr.attrelid
JOIN pg_namespace AS ns ON ns.oid = cls.relnamespace
LEFT OUTER JOIN information_schema.columns AS col ON col.table_schema = nspname AND
     col.table_name = relname AND
     col.column_name = attname
WHERE
    attr.attrelid = {{ parent_id|qtLiteral }}::oid
    {% if clid %}
        AND attr.attnum = {{ clid|qtLiteral }}
    {% endif %}
    {### To show system objects ###}
    {% if not show_sys_objects %}
        AND attr.attnum > 0
    {% endif %}
    AND atttypid <> 0 AND
    relkind IN ('r', 'v', 'm') AND
    NOT attisdropped  
ORDER BY attnum