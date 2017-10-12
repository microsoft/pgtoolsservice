{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{#========Below will provide rule id for last created rule========#}
{% if rule_name %}
SELECT
    rw.oid
FROM
    pg_rewrite rw
WHERE
    rw.rulename={{ rule_name|qtLiteral }}
{% endif %}
