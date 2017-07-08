{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT cls.oid,
    cls.relname as name,
    indnatts,
    amname,
    CASE WHEN length(spcname) > 0 THEN spcname ELSE
        (SELECT sp.spcname FROM pg_database dtb
        JOIN pg_tablespace sp ON dtb.dattablespace=sp.oid
        WHERE dtb.oid = {{ did }}::oid)
    END as spcname,
    CASE contype
        WHEN 'p' THEN desp.description
        WHEN 'u' THEN desp.description
        WHEN 'x' THEN desp.description
        ELSE des.description
    END AS comment,
    condeferrable,
    condeferred,
    substring(array_to_string(cls.reloptions, ',') from 'fillfactor=([0-9]*)') AS fillfactor
FROM pg_index idx
JOIN pg_class cls ON cls.oid=indexrelid
JOIN pg_class tab ON tab.oid=indrelid
LEFT OUTER JOIN pg_tablespace ta on ta.oid=cls.reltablespace
JOIN pg_namespace n ON n.oid=tab.relnamespace
JOIN pg_am am ON am.oid=cls.relam
LEFT JOIN pg_depend dep ON (dep.classid = cls.tableoid AND dep.objid = cls.oid AND dep.refobjsubid = '0' AND dep.refclassid=(SELECT oid FROM pg_class WHERE relname='pg_constraint') AND dep.deptype='i')
LEFT OUTER JOIN pg_constraint con ON (con.tableoid = dep.refclassid AND con.oid = dep.refobjid)
LEFT OUTER JOIN pg_description des ON (des.objoid=cls.oid AND des.classoid='pg_class'::regclass)
LEFT OUTER JOIN pg_description desp ON (desp.objoid=con.oid AND desp.objsubid = 0 AND desp.classoid='pg_constraint'::regclass)
WHERE indrelid = {{tid}}::oid
{% if cid %}
AND cls.oid = {{cid}}::oid
{% endif %}
AND contype='x'
ORDER BY cls.relname