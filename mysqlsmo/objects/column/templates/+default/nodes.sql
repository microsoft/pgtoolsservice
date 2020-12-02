{# 
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#}

SELECT
    COLUMN_NAME as name,
    DATA_TYPE as type,
    ORDINAL_POSITION as ordinal,
    COLUMN_DEFAULT as column_default, 
    IS_NULLABLE as is_nullable,
    COLUMN_KEY as column_key,
    EXTRA as extra,
    TRUE AS is_updatable
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = {{dbname|string_convert}} AND TABLE_NAME = {{tbl_name|string_convert}};