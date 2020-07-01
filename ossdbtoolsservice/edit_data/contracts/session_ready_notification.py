# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.serialization import Serializable


class SessionReadyNotificationParams(Serializable):
    """
    Parameters to be sent back with a edit session ready event
    Attributes:
        owner_uri:          URI for the editor that owns the query
        batch_summaries:    Summaries of the result sets that were returned with the query
    """

    def __init__(self, owner_uri: str, success: bool, message: str):
        self.owner_uri: str = owner_uri
        self.success: bool = success
        self.message: str = message


SESSION_READY_NOTIFICATION = 'edit/sessionReady'
