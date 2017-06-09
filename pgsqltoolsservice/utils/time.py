# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Utility functions for operating with datetimes"""

from datetime import datetime #noaq

def get_time_str(time: datetime):
    """Convert a time object into a standard user-readable string"""
    return time.strftime('%H:%M:%S.%f')


def get_elapsed_time_str(start_time: datetime, end_time: datetime):
    """Get time difference between two times as a user-readable string"""
    elapsed_time = end_time - start_time
    return str(elapsed_time)
