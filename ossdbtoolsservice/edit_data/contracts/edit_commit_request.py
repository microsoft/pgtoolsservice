# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.edit_data.contracts import SessionOperationRequest
from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)


class EditCommitRequest(SessionOperationRequest):
    def __init__(self):
        SessionOperationRequest.__init__(self)


class EditCommitResponse:
    def __init__(self):
        pass


EDIT_COMMIT_REQUEST = IncomingMessageConfiguration("edit/commit", EditCommitRequest)
OutgoingMessageRegistration.register_outgoing_message(EditCommitResponse)
