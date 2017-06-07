# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Utility functions for the PostgreSQL Tools Service"""

import inflection
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


def deserialize_from_dict(class_, dictionary, **kwargs):
    """
    Deserializes a class from a json-derived dictionary using attribute name normalization.
    Attributes described in **kwargs will be omitted from automatic attribute definition and the
    provided method will be called to deserialize the value
    :param class_: Class to create an instance of
    :param dictionary: Dictionary of values to assign attributes with
    :param kwargs: Class to call .from_dict on when the argument key is found in the dictionary
    :raises AttributeError: When the class does not contain an attribute in the dictionary
    :return: An instance of class_ with attributes assigned
    """
    # Create an instance of the class
    instance = class_()
    instance_attributes = dir(instance)

    for attr in dictionary:
        # Convert the attribute name to a snake-cased, pythonic attribute name
        pythonic_attr = inflection.underscore(attr)

        # Make sure that the attribute is in the directory for the instance
        if pythonic_attr not in instance_attributes:
            raise AttributeError('Could not deserialize to class {}, {} is not defined as an attribute'
                                 .format(class_, pythonic_attr))

        # If the kwargs includes a function for deserializing this attribute, use it
        if pythonic_attr in kwargs:
            setattr(instance, pythonic_attr, kwargs[pythonic_attr].from_dict(dictionary[attr]))
        else:
            setattr(instance, pythonic_attr, dictionary[attr])

    return instance
