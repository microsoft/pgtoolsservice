# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Utility functions for validating parameters"""


def is_not_none(param_name: str, value_to_check: any) -> None:
    """
    Validates that an object is not None, raises ValueError if it is
    :param param_name: The name of the parameter to validate
    :param value_to_check: The value to check for None
    """
    if value_to_check is None:
        # TODO: Localize
        raise ValueError(u"{} is None".format(param_name))


def is_within_range(param_name: str, value_to_check: float, lower_limit: float, upper_limit: float) -> None:
    """
    Raises ValueError if the value is outside of the given lower and upper limits (exclusive)
    :param param_name: Name of the parameter to validate
    :param value_to_check: Value to check for compliance
    :param lower_limit: Lower limit to validate against, exclusive
    :param upper_limit: Upper limit to validate against, exclusive
    """
    if value_to_check < lower_limit or value_to_check > upper_limit:
        # TODO: Localize
        raise ValueError(u"Value for {} is not between {} and {}".format(param_name, lower_limit, upper_limit))


def is_less_than(param_name: str, value_to_check: float, upper_limit: float) -> None:
    """
    Raises ValueError if the value is greater than or equal to the given upper limit
    :param param_name: Name of the parameter to validate
    :param value_to_check: Value to check for compliance
    :param upper_limit: Upper limit to validate against 
    """
    if value_to_check >= upper_limit:
        # TODO: Localize
        raise ValueError(u"Value for {} is greater than or equal to {}".format(param_name, upper_limit))


def is_greater_than(param_name: str, value_to_check: float, lower_limit: float) -> None:
    """
    Raises ValueError if the value is less than or equal to the given upper limit
    :param param_name: Name of the parameter to validate
    :param value_to_check: Value to check for compliance
    :param lower_limit: Lower limit to validate against 
    """
    if value_to_check <= lower_limit:
        # TODO: Localize
        raise ValueError(u"Value for {} is less than or equal to {}".format(param_name, lower_limit))


def is_not_equal(param_name: str, value_to_check: any, undesired_value: any) -> None:
    """
    Raises ValueError if the value is equal to the undesired value
    :param param_name: Name of the parameter to validate 
    :param value_to_check: Value to check for undesired values
    :param undesired_value: Value that value_to_check should not equal
    """
    if value_to_check == undesired_value:
        raise ValueError(
            u"The given value for {} '{}' should not equal '{}'".format(
                param_name,
                value_to_check,
                undesired_value
            )
        )


def is_not_none_or_empty(param_name: str, value_to_check: str) -> None:
    """
    Raises ValueError if the value is None or an empty string
    :param param_name: The name of the parameter being validated
    :param value_to_check: The value of the parameter being validated
    """
    if value_to_check is None or value_to_check == '':
        raise ValueError(u"Parameter {} contains a None or empty string".format(param_name))


def is_not_none_or_whitespace(param_name: str, value_to_check: str) -> None:
    """
    Raises ValueError if the value is None or a whitespace/empty string
    :param param_name: Name of the parameter to validate
    :param value_to_check: Value to of the parameter being validated 
    """
    if value_to_check is None or value_to_check.strip() == '':
        raise ValueError(u"Parameter {} contains a None, empty, or whitespace string".format(param_name))
