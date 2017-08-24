# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from pgsqltoolsservice.edit_data.contracts import EditCell


class EditCellResponse():

    def __init__(self, edit_cell: EditCell, is_row_dirty: bool):
        self.cell = edit_cell
        self.is_row_dirty = is_row_dirty
