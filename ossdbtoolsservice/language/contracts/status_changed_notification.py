# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds contracts for the status change notification"""

from ossdbtoolsservice.serialization import Serializable
from ossdbtoolsservice.hosting import OutgoingMessageRegistration

class StatusChangeParams(Serializable):
    owner_uri: str
    status: str

    def __init__(self, owner_uri=None, status=None):
        self.owner_uri: str = owner_uri
        self.status: str = status


STATUS_CHANGE_NOTIFICATION = 'textDocument/statusChanged'

OutgoingMessageRegistration.register_outgoing_message(StatusChangeParams)