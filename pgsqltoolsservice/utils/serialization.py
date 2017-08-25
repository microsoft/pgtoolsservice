# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Utility function for serialization"""

import enum
import json

import inflection


def convert_to_dict(obj):
    """
    Serializes an object to a json-ready dictionary using attribute name normalization. The
    serialization is repeated, recursively until a built-in type is returned
    :param obj: The object to convert to a jsonic dictionary
    :return: A json-ready dictionary representation of the object
    """
    return json.loads(json.dumps(obj, default=_get_serializable_value))


def _get_serializable_value(obj):
    """Gets a serializable representation of an object, for use as the default argument to json.dumps"""
    # If the object is an Enum, use its value
    if isinstance(obj, enum.Enum):
        return _get_serializable_value(obj.value)
    # Try to use the object's dictionary representation if available
    try:
        return {inflection.camelize(key, False): value for key, value in obj.__dict__.items()}
    except AttributeError:
        pass
    # Assume the object can be serialized normally
    try:
        json.dumps(obj)
        return obj
    except BaseException:
        return None
