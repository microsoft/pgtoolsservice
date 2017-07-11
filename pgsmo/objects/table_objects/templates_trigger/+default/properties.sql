{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT t.oid,t.tgname AS name, t.xmin, t.*, relname, CASE WHEN relkind = 'r' THEN TRUE ELSE FALSE END AS parentistable,
    nspname, des.description, l.lanname, p.prosrc, p.proname AS tfunction,
    COALESCE(substring(pg_get_triggerdef(t.oid), 'WHEN (.*) EXECUTE PROCEDURE'),
    substring(pg_get_triggerdef(t.oid), 'WHEN (.*)  \\$trigger')) AS whenclause,
    -- We need to convert tgargs column bytea datatype to array datatype
    (string_to_array(encode(tgargs, 'escape'), '\000')::text[])[1:tgnargs] AS custom_tgargs,
{% if datlastsysoid %}
    (CASE WHEN t.oid <= {{ datlastsysoid}}::oid THEN true ElSE false END) AS is_sys_trigger,
{% endif %}
    (CASE WHEN tgconstraint != 0::OID THEN true ElSE false END) AS is_constarint,
    (CASE WHEN tgenabled = 'O' THEN true ElSE false END) AS is_enable_trigger
FROM pg_trigger t
    JOIN pg_class cl ON cl.oid=tgrelid
    JOIN pg_namespace na ON na.oid=relnamespace
    LEFT OUTER JOIN pg_description des ON (des.objoid=t.oid AND des.classoid='pg_trigger'::regclass)
    LEFT OUTER JOIN pg_proc p ON p.oid=t.tgfoid
    LEFT OUTER JOIN pg_language l ON l.oid=p.prolang
WHERE NOT tgisinternal
    AND tgrelid = {{tid}}::OID
{% if trid %}
    AND t.oid = {{trid}}::OID
{% endif %}
ORDER BY tgname;
