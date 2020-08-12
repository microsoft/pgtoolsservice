{# 
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#}
SELECT 
    TRIGGER_NAME as name,
    TRIGGER_SCHEMA as dbname
FROM information_schema.TRIGGERS
WHERE TRIGGER_SCHEMA = {{dbname|string_convert}} AND EVENT_OBJECT_TABLE={{tbl_name|string_convert}};