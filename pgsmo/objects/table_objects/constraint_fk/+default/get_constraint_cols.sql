{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% for keypair in keys %}
{% if loop.index != 1 %}
UNION
{% endif %}
SELECT a1.attname as conattname,
    a2.attname as confattname
FROM pg_attribute a1,
    pg_attribute a2
WHERE a1.attrelid={{tid}}::oid
    AND a1.attnum={{keypair[1]}}
    AND a2.attrelid={{confrelid}}::oid
    AND a2.attnum={{keypair[0]}}
{% endfor %}