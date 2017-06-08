# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Utility function for serialization"""

import enum
import json

import inflection


def convert_from_dict(class_, dictionary, **kwargs):
    """
    Converts a class from a json-derived dictionary using attribute name normalization.
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
    return obj
