{# 
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#}
SELECT 
    ROUTINE_NAME as name,
    ROUTINE_SCHEMA as dbname
FROM information_schema.ROUTINES
WHERE ROUTINE_TYPE = 'PROCEDURE' AND ROUTINE_SCHEMA = {{dbname|string_convert}};