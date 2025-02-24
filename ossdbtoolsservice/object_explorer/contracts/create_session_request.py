# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pydantic import BaseModel, Field

from ossdbtoolsservice.connection.contracts import ConnectionDetails
from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)


class CreateSessionResponse(BaseModel):
    session_id: str = Field(alias="sessionId")


CREATE_SESSION_REQUEST = IncomingMessageConfiguration(
    "objectexplorer/createsession", ConnectionDetails
)
OutgoingMessageRegistration.register_outgoing_message(CreateSessionResponse)
