{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT COUNT(1)
FROM pg_depend dep
    JOIN pg_class cl ON dep.classid=cl.oid AND relname='pg_rewrite'
    WHERE refobjid= {{tid}}::oid
    AND classid='pg_class'::regclass
    AND refobjsubid= {{clid|qtLiteral}};
