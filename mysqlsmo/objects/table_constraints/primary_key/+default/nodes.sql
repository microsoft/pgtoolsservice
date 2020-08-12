{# 
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#}

SELECT
    COLUMN_NAME as name
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = {{dbname | string_convert}}
AND TABLE_NAME = {{tbl_name | string_convert}}
AND CONSTRAINT_NAME = 'PRIMARY';