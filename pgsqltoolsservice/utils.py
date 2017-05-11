# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Utility functions for the PostgreSQL Tools Service"""

import json
from enum import Enum


def get_serializable_value(obj):
    """For use as the default argument to json.dumps"""
    # If the object is an Enum, use its value
    if isinstance(obj, Enum):
        return get_serializable_value(obj.value)
    # Try to use the object's dictionary representation if available
    try:
        return obj.__dict__
    except AttributeError:
        pass
    # If the object can be serialized normally, return it. Otherwise ignore it
    try:
        json.dumps(obj)
        return obj
    except TypeError:
        return None


def object_to_dictionary(obj):
    """Convert an object to a dictionary representation"""
    return json.loads(json.dumps(obj, default=get_serializable_value))
