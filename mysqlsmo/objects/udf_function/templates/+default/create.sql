{# 
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#}
CREATE FUNCTION IF NOT EXISTS {{fn_name}} RETURNS {{ret}} SONAME {{dl | string_convert}};