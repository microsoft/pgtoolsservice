# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds contracts for the status change notification"""

from ossdbtoolsservice.hosting import OutgoingMessageRegistration
from ossdbtoolsservice.serialization import Serializable


class StatusChangeParams(Serializable):
    owner_uri: str | None
    status: str | None

    def __init__(self, owner_uri: str | None = None, status: str | None = None) -> None:
        self.owner_uri = owner_uri
        self.status = status


STATUS_CHANGE_NOTIFICATION = "textDocument/statusChanged"

OutgoingMessageRegistration.register_outgoing_message(StatusChangeParams)
