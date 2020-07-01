# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.edit_data.contracts import RowOperationRequest, EditCellResponse, EditCell


class RevertCellRequest(RowOperationRequest):

    def __init__(self):
        RowOperationRequest.__init__(self)
        self.column_id: int = None


class RevertCellResponse(EditCellResponse):

    def __init__(self, edit_cell: EditCell, is_row_dirty: bool):
        EditCellResponse.__init__(self, edit_cell, is_row_dirty)


REVERT_CELL_REQUEST = IncomingMessageConfiguration('edit/revertCell', RevertCellRequest)
