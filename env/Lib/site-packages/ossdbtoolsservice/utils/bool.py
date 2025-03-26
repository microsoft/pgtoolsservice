# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Utility functions for operating with booleans"""


def str_to_bool(value: str) -> bool:
    """Convert a string to a boolean"""
    return str(value).strip().lower() in ("true", "yes", "1")


def bool_to_str(value: bool) -> str:
    """Convert a boolean to a string"""
    return "true" if value else "false"
