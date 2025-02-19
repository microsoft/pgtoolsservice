# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.connection.contracts import ConnectionDetails
from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)
from ossdbtoolsservice.serialization import Serializable


class CreateSessionResponse(Serializable):
    session_id: str

    def __init__(self, session_id: str) -> None:
        self.session_id: str = session_id


CREATE_SESSION_REQUEST = IncomingMessageConfiguration(
    "objectexplorer/createsession", ConnectionDetails
)
OutgoingMessageRegistration.register_outgoing_message(CreateSessionResponse)
