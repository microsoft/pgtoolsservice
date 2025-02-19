# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.edit_data.contracts import SessionOperationRequest
from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)


class DisposeRequest(SessionOperationRequest):
    def __init__(self) -> None:
        super().__init__()


class DisposeResponse:
    def __init__(self) -> None:
        pass


DISPOSE_REQUEST = IncomingMessageConfiguration("edit/dispose", DisposeRequest)
OutgoingMessageRegistration.register_outgoing_message(DisposeResponse)
