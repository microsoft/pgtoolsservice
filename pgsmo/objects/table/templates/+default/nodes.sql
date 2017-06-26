{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT rel.oid, rel.relname AS name,
    (SELECT count(*) FROM pg_trigger WHERE tgrelid=rel.oid) AS triggercount,
    (SELECT count(*) FROM pg_trigger WHERE tgrelid=rel.oid AND tgenabled = 'O') AS has_enable_triggers
FROM pg_class rel
    WHERE rel.relkind IN ('r','s','t') AND rel.relnamespace = {{ scid }}::oid
    {% if tid %} AND rel.oid = {{tid}}::OID {% endif %}
    ORDER BY rel.relname;
