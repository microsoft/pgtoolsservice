{# 
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#}
SELECT
    EVENT_NAME as name,
    EVENT_SCHEMA as dbname
FROM information_schema.EVENTS
WHERE EVENT_SCHEMA = {{dbname|string_convert}};