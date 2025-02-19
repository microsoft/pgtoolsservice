# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.edit_data.contracts import (
    EditCell,
    EditCellResponse,
    RowOperationRequest,
)
from ossdbtoolsservice.hosting import IncomingMessageConfiguration


class RevertCellRequest(RowOperationRequest):
    column_id: int | None

    def __init__(self) -> None:
        RowOperationRequest.__init__(self)
        self.column_id: int | None = None


class RevertCellResponse(EditCellResponse):
    def __init__(self, edit_cell: EditCell | None, is_row_dirty: bool) -> None:
        EditCellResponse.__init__(self, edit_cell, is_row_dirty)


REVERT_CELL_REQUEST = IncomingMessageConfiguration("edit/revertCell", RevertCellRequest)
