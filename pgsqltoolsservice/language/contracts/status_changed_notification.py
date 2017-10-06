# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds contracts for the status change notification"""

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.serialization import Serializable


class StatusChangeParams(Serializable):
    """
    Parameters for the Status Change notification
    """
    @classmethod
    def from_data(cls, owner_uri: str, status: str):
        obj = cls()
        obj.owner_uri = owner_uri
        obj.status = status
        return obj

    def __init__(self):
        self.owner_uri: str = None
        self.status: str = None


STATUS_CHANGE_NOTIFICATION = 'textDocument/statusChanged'
