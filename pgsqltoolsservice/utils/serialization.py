# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Utility function for serialization"""

import enum
import json

import inflection


def convert_from_dict(class_, dictionary, ignore_extra_attributes=False, **kwargs):
    """
    Converts a class from a json-derived dictionary using attribute name normalization.
    Attributes described in **kwargs will be omitted from automatic attribute definition and the
    provided method will be called to deserialize the value
    :param class_: Class to create an instance of
    :param dictionary: Dictionary of values to assign attributes with
    :param ignore_extra_attributes: Whether to ignore extra attributes when converting instead of raising an error
    :param kwargs: Class to call .from_dict on when the argument key is found in the dictionary
    :raises AttributeError: When the class does not contain an attribute in the dictionary
    :return: An instance of class_ with attributes assigned
    """
    # Create an instance of the class
    instance = class_()
    instance_attributes = dir(instance)

    if dictionary is None:
        return None

    for attr in dictionary:
        # Convert the attribute name to a snake-cased, pythonic attribute name
        pythonic_attr = inflection.underscore(attr)

        # If an unknown attribute is provided, raise an error unless set to ignore it
        if pythonic_attr not in instance_attributes:
            if ignore_extra_attributes:
                continue
            raise AttributeError('Could not deserialize to class {}, {} is not defined as an attribute'
                                 .format(class_, pythonic_attr))

        value = dictionary[attr]
        if pythonic_attr in kwargs:
            # Caller provided a class to deserialize to. Use that
            if isinstance(value, list):
                # Value is a list. Use a list comprehension to deserialize all instances
                deserialized_value = [kwargs[pythonic_attr].from_dict(x) for x in dictionary[attr]]
            elif issubclass(kwargs[pythonic_attr], enum.Enum):
                # Value is an enum. Convert it from a string
                deserialized_value = kwargs[pythonic_attr](value)
            else:
                # Value is a singlar object. Use the class to deserialize
                deserialized_value = kwargs[pythonic_attr].from_dict(dictionary[attr])
        else:
            # Object can be assigned directly
            deserialized_value = dictionary[attr]

        # Store the value in the instance of the object
        setattr(instance, pythonic_attr, deserialized_value)

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
    try:
        json.dumps(obj)
        return obj
    except BaseException:
        return None
