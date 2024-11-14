# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.edit_data.contracts import RowOperationRequest, EditCellResponse


class UpdateCellRequest(RowOperationRequest):
    column_id: int
    new_value: str

    def __init__(self):
        RowOperationRequest.__init__(self)
        self.column_id = None
        self.new_value = None


class UpdateCellResponse(EditCellResponse):

    def __init__(self):
        EditCellResponse.__init__(self)


UPDATE_CELL_REQUEST = IncomingMessageConfiguration('edit/updateCell', UpdateCellRequest)
