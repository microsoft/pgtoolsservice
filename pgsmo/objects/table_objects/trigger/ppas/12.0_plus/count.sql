{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT COUNT(*)
FROM pg_catalog.pg_trigger t
    WHERE NOT tgisinternal
    AND tgrelid = {{tid}}::OID
    AND tgpackageoid = 0
