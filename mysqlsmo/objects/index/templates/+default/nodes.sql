{# 
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#}

SELECT 
    INDEX_NAME as index_name,
    COLUMN_NAME as col_name
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = {{dbname|string_convert}} AND TABLE_NAME = {{tbl_name|string_convert}};