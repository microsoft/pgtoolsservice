# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.edit_data.contracts import RowOperationRequest
from ossdbtoolsservice.hosting import IncomingMessageConfiguration


class RevertRowRequest(RowOperationRequest):
    def __init__(self) -> None:
        super().__init__()


class RevertRowResponse:
    def __init__(self) -> None:
        pass


REVERT_ROW_REQUEST = IncomingMessageConfiguration("edit/revertRow", RevertRowRequest)
