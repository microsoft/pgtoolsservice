# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.edit_data.contracts import RowOperationRequest
from ossdbtoolsservice.hosting import IncomingMessageConfiguration


class DeleteRowRequest(RowOperationRequest):
    def __init__(self):
        RowOperationRequest.__init__(self)


class DeleteRowResponse:
    def __init__(self):
        pass


DELETE_ROW_REQUEST = IncomingMessageConfiguration("edit/deleteRow", DeleteRowRequest)
