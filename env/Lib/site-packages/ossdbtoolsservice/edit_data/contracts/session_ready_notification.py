# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.hosting import OutgoingMessageRegistration
from ossdbtoolsservice.serialization import Serializable


class SessionReadyNotificationParams(Serializable):
    """
    Parameters to be sent back with a edit session ready event
    Attributes:
        owner_uri:          URI for the editor that owns the query
        batch_summaries:    Summaries of the result sets that were returned with the query
    """

    owner_uri: str
    success: bool
    message: str | None

    def __init__(self, owner_uri: str, success: bool, message: str | None) -> None:
        self.owner_uri: str = owner_uri
        self.success: bool = success
        self.message: str | None = message


SESSION_READY_NOTIFICATION = "edit/sessionReady"

OutgoingMessageRegistration.register_outgoing_message(SessionReadyNotificationParams)
