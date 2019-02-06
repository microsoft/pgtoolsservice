# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def get_attribute_value(owner_uri: str, attribute_name: str):
    """Get attribute value for given attribute name from the owner uri"""
    if owner_uri is not None and '/' in owner_uri:
        sliced_owner_uri = owner_uri[owner_uri.rindex('/'):len(owner_uri)]
        splited_owner_uri = sliced_owner_uri.split('|')
        for item in splited_owner_uri:
            if attribute_name in item:
                final_value = item.split(':')
                return final_value[1]
