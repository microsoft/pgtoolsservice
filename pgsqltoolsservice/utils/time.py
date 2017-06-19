# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Utility functions for operating with datetimes"""

from datetime import datetime  # noqa


def get_time_str(time: datetime):
    """Convert a time object into a standard user-readable string"""
    if time is None:
        return None
    return time.strftime('%H:%M:%S.%f')


def get_elapsed_time_str(start_time: datetime, end_time: datetime):
    """Get time difference between two times as a user-readable string"""
    if start_time is None or end_time is None:
        return None
    elapsed_time = end_time - start_time
    return str(elapsed_time)
