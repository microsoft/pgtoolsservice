{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT att.attname as name
FROM pg_attribute att
    WHERE att.attrelid = {{tid}}::oid
    AND att.attnum IN ({{ clist }})
    AND att.attisdropped IS FALSE
    ORDER BY att.attnum