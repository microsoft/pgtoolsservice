# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)
from ossdbtoolsservice.schema.contracts.common import SessionIdContainer

CREATE_SESSION_REQUEST = IncomingMessageConfiguration(
    "schemaDesigner/createSession", SessionIdContainer
)

CLOSE_SESSION_REQUEST = IncomingMessageConfiguration(
    "schemaDesigner/closeSession", SessionIdContainer
)

CREATE_SESSION_COMPLETE = "schemaDesigner/sessionCreated"

OutgoingMessageRegistration.register_outgoing_message(SessionIdContainer)

__all__ = [
    "CREATE_SESSION_REQUEST",
    "CLOSE_SESSION_REQUEST",
    "CREATE_SESSION_COMPLETE",
]