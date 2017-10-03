# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Dict, List  # noqa

from pgsqltoolsservice.edit_data.update_management import RowEdit, CellUpdate, EditScript
from pgsqltoolsservice.query import ResultSet
from pgsqltoolsservice.edit_data import EditTableMetadata
from pgsqltoolsservice.edit_data.contracts import EditCellResponse, EditCell, RevertCellResponse, EditRow, EditRowState
from pgsqltoolsservice.query.contracts import DbCellValue


class RowUpdate(RowEdit):

    def __init__(self, row_id: int, result_set: ResultSet, table_metadata: EditTableMetadata):
        super(RowUpdate, self).__init__(row_id, result_set, table_metadata)
        self.row = result_set.get_row(row_id)
        self._cell_updates: Dict[int, CellUpdate] = {}

    def set_cell_value(self, column_index: int, new_value: str) -> EditCellResponse:
        self.validate_column_is_updatable(column_index)
        cell_update = CellUpdate(self.result_set.columns_info[column_index], new_value)

        if cell_update.value is self.row[column_index].raw_object:
            existing_cell_update = self._cell_updates.get(column_index)
            if existing_cell_update is not None:
                self._cell_updates.pop(column_index)

            return EditCellResponse(EditCell(self.row[column_index], False, self.row_id), len(self._cell_updates) > 0)

        self._cell_updates[column_index] = cell_update

        return EditCellResponse(cell_update.as_edit_cell, True)

    def get_edit_row(self, cached_row: List[DbCellValue]) -> EditRow:

        edit_cells = [EditCell(cell, True, self.row_id) for cell in cached_row]

        for column_index, cell in self._cell_updates.items():
            edit_cells[column_index] = cell.edit_cell

        return EditRow(self.row_id, edit_cells, EditRowState.DIRTY_UPDATE)

    def revert_cell_value(self, column_index: int) -> RevertCellResponse:

        self._cell_updates.pop(column_index)
        return RevertCellResponse(EditCell(self.row[column_index], False, self.row_id), len(self._cell_updates) > 0)

    def get_script(self) -> EditScript:

        query = 'UPDATE {0} SET {1} {2} RETURNING *'
        set_template = '"{0}" = %s'
        set_query = []
        cell_values = []
        for cell in self._cell_updates.values():
            cell_values.append(cell.value)
            set_query.append(set_template.format(cell.column.column_name))

        set_join = ', '.join(set_query)

        where_script = self.build_where_clause()
        query_template = query.format(self.table_metadata.multipart_name, set_join, where_script.query_template)
        cell_values.extend(where_script.query_paramters)

        return EditScript(query_template, cell_values)

    def apply_changes(self, cursor):
        self.result_set.update_row(self.row_id, cursor)
