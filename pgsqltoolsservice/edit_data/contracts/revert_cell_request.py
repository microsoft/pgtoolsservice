# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.edit_data.contracts import RowOperationRequest, EditCellResponse


class RevertCellRequest(RowOperationRequest):

    def __init__(self):
        RowOperationRequest.__init__(self)
        self.column_id: int = None


class RevertCellResponse(EditCellResponse):

    def __init__(self):
        pass


REVERT_CELL_REQUEST = IncomingMessageConfiguration('edit/revertCell', RevertCellRequest)
