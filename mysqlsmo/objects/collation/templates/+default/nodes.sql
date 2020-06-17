{# 
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#}

SELECT
    COLLATION_NAME as name
FROM INFORMATION_SCHEMA.COLLATIONS
WHERE CHARACTER_SET_NAME = {{char_name | string_convert}};