{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{### Input/Output/Send/Receive/Analyze function list also append into TypModeIN/TypModOUT ###}
{% if extfunc %}
SELECT proname, nspname,
    CASE WHEN (length(nspname) > 0 AND nspname != 'public') and length(proname) > 0  THEN
        concat(quote_ident(nspname), '.', quote_ident(proname))
    WHEN length(proname) > 0 THEN
        quote_ident(proname)
    ELSE '' END AS func
FROM (
    SELECT proname, nspname, max(proargtypes[0]) AS arg0, max(proargtypes[1]) AS arg1
FROM pg_proc p
    JOIN pg_namespace n ON n.oid=pronamespace
GROUP BY proname, nspname
HAVING count(proname) = 1) AS uniquefunc
WHERE arg0 <> 0 AND (arg1 IS NULL OR arg1 <> 0);
{% endif %}
{### TypmodIN list ###}
{% if typemodin %}
SELECT proname, nspname,
    CASE WHEN length(nspname) > 0 AND length(proname) > 0  THEN
        concat(quote_ident(nspname), '.', quote_ident(proname))
    ELSE '' END AS func
FROM pg_proc p
    JOIN pg_namespace n ON n.oid=pronamespace
WHERE prorettype=(SELECT oid FROM pg_type WHERE typname='int4')
    AND proargtypes[0]=(SELECT oid FROM pg_type WHERE typname='_cstring')
    AND proargtypes[1] IS NULL
ORDER BY nspname, proname;
{% endif %}
{### TypmodOUT list ###}
{% if typemodout %}
SELECT proname, nspname,
    CASE WHEN length(nspname) > 0 AND length(proname) > 0  THEN
        concat(quote_ident(nspname), '.', quote_ident(proname))
    ELSE '' END AS func
FROM pg_proc p
    JOIN pg_namespace n ON n.oid=pronamespace
WHERE prorettype=(SELECT oid FROM pg_type WHERE typname='cstring')
    AND proargtypes[0]=(SELECT oid FROM pg_type WHERE typname='int4')
    AND proargtypes[1] IS NULL
ORDER BY nspname, proname;
{% endif %}
