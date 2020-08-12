{# 
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#}
SELECT
    GRANTEE as name
FROM information_schema.USER_PRIVILEGES
GROUP BY GRANTEE;