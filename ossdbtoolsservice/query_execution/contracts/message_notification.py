# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.core.models import PGTSBaseModel
from ossdbtoolsservice.hosting import OutgoingMessageRegistration


class ResultMessage(PGTSBaseModel):
    batch_id: int | None = None
    is_error: bool
    time: str | None = None
    message: str


class MessageNotificationParams(PGTSBaseModel):
    """
    Parameters to be sent back with a message notification
    Attributes:
        owner_uri:  URI for the editor that owns the query
        message:    The message that is being returned
    """

    owner_uri: str
    message: ResultMessage


MESSAGE_NOTIFICATION = "query/message"

DEPLOY_MESSAGE_NOTIFICATION = "query/deployMessage"

OutgoingMessageRegistration.register_outgoing_message(MessageNotificationParams)
OutgoingMessageRegistration.register_outgoing_message(ResultMessage)
