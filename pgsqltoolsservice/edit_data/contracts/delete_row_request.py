# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.edit_data.contracts import SessionOperationRequest


class DeleteRowRequest(SessionOperationRequest):

    def __init__(self):
        SessionOperationRequest.__init__(self)


class DeleteRowResponse:

    def __init__(self):
        pass


DELETE_ROW_REQUEST = IncomingMessageConfiguration('edit/deleteRow', DeleteRowRequest)
