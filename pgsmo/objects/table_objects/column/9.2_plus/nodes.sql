{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
 SELECT
  attname AS name,
  attnum AS OID,
  typ.oid AS typoid,
  typ.typname AS datatype,
  attnotnull AS not_null,
  attr.atthasdef AS has_default_val,
  nspname,
  relname,
  attrelid,
  CASE WHEN typ.typtype = 'd' THEN typ.typtypmod ELSE atttypmod END AS typmod,
  CASE WHEN atthasdef THEN (SELECT pg_get_expr(adbin, cls.oid) FROM pg_attrdef WHERE adrelid = cls.oid AND adnum = attr.attnum) ELSE NULL END AS default,
  TRUE AS is_updatable,
  EXISTS (SELECT 1 FROM unnest(con.conkey) AS conkey(att) WHERE attr.attnum = conkey.att) AS isunique,
  -- Add this expression to show if each column is a primary key column
  EXISTS (SELECT 1 FROM unnest(idx.indkey) AS indkey(att) WHERE attr.attnum = indkey.att) AS isprimarykey /* Can't do ANY() on pg_index.indkey which is int2vector */
FROM pg_attribute AS attr
JOIN pg_type AS typ ON attr.atttypid = typ.oid
JOIN pg_class AS cls ON cls.oid = attr.attrelid
JOIN pg_namespace AS ns ON ns.oid = cls.relnamespace
LEFT OUTER JOIN information_schema.columns AS col ON col.table_schema = nspname AND
col.table_name = relname AND
col.column_name = attname
-- Join with pg_index and pg_constraint to get primary key information
JOIN pg_index AS idx ON idx.indrelid = cls.oid AND idx.indisprimary
JOIN pg_constraint AS con ON con.conrelid = cls.oid AND con.conindid = idx.indexrelid AND con.contype = 'p'
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