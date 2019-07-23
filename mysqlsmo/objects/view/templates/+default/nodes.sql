{# 
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#}

SELECT 
    TABLE_NAME as name
FROM information_schema.TABLES
WHERE TABLE_TYPE = 'VIEW' AND TABLE_SCHEMA = {{dbname | string_convert}};