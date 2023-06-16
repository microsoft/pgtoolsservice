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
  TRUE AS is_updatable, /* Supported only since PG 8.2 */
  -- Add this expression to show if each column is a primary key column. Can't do ANY() on pg_index.indkey which is int2vector
  CASE WHEN EXISTS (SELECT * FROM information_schema.key_column_usage WHERE table_schema = nspname AND table_name = relname AND column_name = attname) THEN TRUE ELSE FALSE END AS isprimarykey,
  CASE WHEN EXISTS (SELECT * FROM information_schema.table_constraints WHERE table_schema = nspname AND table_name = relname AND constraint_type = 'UNIQUE' AND constraint_name IN (SELECT constraint_name FROM information_schema.constraint_column_usage WHERE table_schema = nspname AND table_name = relname AND column_name = attname)) THEN TRUE ELSE FALSE END AS isunique 
FROM pg_attribute AS attr
JOIN pg_type AS typ ON attr.atttypid = typ.oid
JOIN pg_class AS cls ON cls.oid = attr.attrelid
JOIN pg_namespace AS ns ON ns.oid = cls.relnamespace
LEFT OUTER JOIN information_schema.columns AS col ON col.table_schema = nspname AND
 col.table_name = relname AND
 col.column_name = attname
WHERE
 attr.attrelid = {{ parent_id }}::oid
 {% if clid %}
 AND attr.attnum = {{ clid }}
 {% endif %}
 {### To show system objects ###}
 {% if not show_sys_objects %}
 AND attr.attnum > 0
 {% endif %}
 AND atttypid <> 0 AND
 relkind IN ('r', 'v', 'm', 'p') AND
 NOT attisdropped 
ORDER BY attnum