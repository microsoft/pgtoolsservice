
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABCMeta
import inflection
import enum


class Serializable(metaclass=ABCMeta):
    @classmethod
    def from_dict(cls, dictionary: dict):
        kwargs = cls.get_child_serializable_types()
        ignore_extra_attributes = cls.ignore_extra_attributes()

        return convert_from_dict(cls, dictionary, ignore_extra_attributes, **kwargs)

    @classmethod
    def get_child_serializable_types(cls):
        return {}

    @classmethod
    def ignore_extra_attributes(cls):
        return False


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

        if pythonic_attr in kwargs and value is not None:
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
            deserialized_value = value

        # Store the value in the instance of the object
        setattr(instance, pythonic_attr, deserialized_value)

    return instance
