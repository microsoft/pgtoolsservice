# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing utilities for cancelling requests"""


class CancellationToken:
    """Token used to indicate if an operation has been canceled"""

    def __init__(self):
        self.canceled = False

    def cancel(self):
        """Mark the cancellation token as canceled"""
        self.canceled = True
