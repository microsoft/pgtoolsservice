# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.query_execution.contracts.common import ResultMessage


class MessageNotificationParams:
    """
    Parameters to be sent back with a message notification
    Attributes:
        owner_uri:  URI for the editor that owns the query
        message:    The message that is being returned
    """

    def __init__(self, owner_uri: str, message: ResultMessage):
        self.owner_uri: str = owner_uri
        self.message: ResultMessage = message

MESSAGE_NOTIFICATION = 'query/message'
