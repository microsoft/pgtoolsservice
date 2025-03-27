# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.connection.contracts import ConnectionDetails
from ossdbtoolsservice.core.models import PGTSBaseModel
from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)
from ossdbtoolsservice.schema.contracts.common import SessionIdContainer

CREATE_SESSION_REQUEST = IncomingMessageConfiguration(
    "schemaDesigner/createSession", ConnectionDetails
)
OutgoingMessageRegistration.register_outgoing_message(SessionIdContainer)

CLOSE_SESSION_REQUEST = IncomingMessageConfiguration(
    "schemaDesigner/closeSession", SessionIdContainer
)

__all__ = [
    "CREATE_SESSION_REQUEST",
    "CLOSE_SESSION_REQUEST",
]