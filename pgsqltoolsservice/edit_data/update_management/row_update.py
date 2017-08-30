# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Dict, List # noqa

from pgsqltoolsservice.edit_data.update_management import RowEdit, CellUpdate
from pgsqltoolsservice.query_execution.result_set import ResultSet
from pgsqltoolsservice.edit_data import EditTableMetadata
from pgsqltoolsservice.edit_data.contracts import EditCellResponse, EditCell


class RowUpdate(RowEdit):

    def __init__(self, row_id: int, result_set: ResultSet, table_metadata: EditTableMetadata):
        super(RowUpdate, self).__init__(row_id, result_set, table_metadata)

        self._cell_updates: Dict[int, CellUpdate] = {}

    def set_cell_value(self, column_index: int, new_value: str) -> EditCellResponse:
        cell_update = CellUpdate(self.result_set.columns[column_index], new_value)

        if cell_update.value is self.row[column_index].raw_object:
            existing_cell_update = self._cell_updates.get(column_index)
            if existing_cell_update is not None:
                self._cell_updates.pop(column_index)

            return EditCellResponse(EditCell(self.row[column_index], False), len(self._cell_updates) > 0)

        self._cell_updates[column_index] = cell_update

        return EditCellResponse(cell_update.edit_cell, True)
