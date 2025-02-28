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


class CreateSessionResponse(PGTSBaseModel):
    session_id: str 


CREATE_SESSION_REQUEST = IncomingMessageConfiguration(
    "objectexplorer/createsession", ConnectionDetails
)
OutgoingMessageRegistration.register_outgoing_message(CreateSessionResponse)
