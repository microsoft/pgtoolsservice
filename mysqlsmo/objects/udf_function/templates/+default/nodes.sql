{# 
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#}
SELECT 
    name as name,
    ret as return_type,
    dl as soname
FROM mysql.func;