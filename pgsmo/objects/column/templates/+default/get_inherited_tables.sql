{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT array_to_string(array_agg(inhrelname), ', ') inhrelname, attrname
FROM
 (SELECT
   inhparent::regclass AS inhrelname,
   a.attname AS attrname
  FROM pg_inherits i
  LEFT JOIN pg_attribute a ON
   (attrelid = inhparent AND attnum > 0)
  WHERE inhrelid = {{tid}}::oid
  ORDER BY inhseqno
 ) a
GROUP BY attrname;