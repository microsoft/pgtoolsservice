# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing contracts for restore operations"""

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils


class RestoreParams:
    """Parameters for a restore request"""
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary, options=RestoreOptions)

    def __init__(self):
        self.owner_uri: str = None
        self.options: RestoreOptions = None


class RestoreOptions:
    """Options for a requested restore"""
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary, ignore_extra_attributes=True)

    def __init__(self):
        self.path: str = None


RESTORE_REQUEST = IncomingMessageConfiguration('disasterrecovery/restore', RestoreParams)
