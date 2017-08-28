# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.edit_data.contracts import SessionOperationRequest


class EditCommitRequest(SessionOperationRequest):

    def __init__(self):
        SessionOperationRequest.__init__(self)


class EditCommitResponse:

    def __init__(self):
        pass


EDIT_COMMIT_REQUEST = IncomingMessageConfiguration('edit/commit', EditCommitRequest)
