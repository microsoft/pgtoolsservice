{# 
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# Refer to: https://mariadb.com/kb/en/library/information-schema-check_constraints-table/
#}

SELECT
    CONSTRAINT_NAME as name, CHECK_CLAUSE
FROM information_schema.CHECK_CONSTRAINTS
WHERE CONSTRAINT_SCHEMA = {{dbname | string_convert}}
AND TABLE_NAME = {{tbl_name | string_convert}};