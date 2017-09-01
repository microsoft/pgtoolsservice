# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import List

from pgsqltoolsservice.edit_data.update_management import RowEdit, EditScript
from pgsqltoolsservice.query_execution.result_set import ResultSet
from pgsqltoolsservice.edit_data import EditTableMetadata
from pgsqltoolsservice.edit_data.update_management import CellUpdate
from pgsqltoolsservice.edit_data.contracts import EditCellResponse, RevertCellResponse, EditRow, EditRowState, EditCell
from pgsqltoolsservice.query_execution.contracts import DbCellValue


class RowCreate(RowEdit):

    def __init__(self, row_id: int, result_set: ResultSet, table_metadata: EditTableMetadata):
        super(RowCreate, self).__init__(row_id, result_set, table_metadata)
        self.new_cells: List[CellUpdate] = [None] * len(result_set.columns)

    def set_cell_value(self, column_index: int, new_value: str) -> EditCellResponse:

        self.validate_column_is_updatable(column_index)

        cell_update = CellUpdate(self.result_set.columns[column_index], new_value)
        self.new_cells[column_index] = cell_update

        return EditCellResponse(cell_update.as_edit_cell, True)

    def revert_cell_value(self, column_index: int) -> RevertCellResponse:
        self.new_cells[column_index] = None
        return RevertCellResponse(None, True)

    def get_edit_row(self, cached_row: List[DbCellValue]) -> EditRow:

        edit_cells = []
        for cell in self.new_cells:
            db_cell_value = DbCellValue('', False, None, self.row_id) if cell is None else cell.as_db_cell_value
            edit_cells.append(EditCell(db_cell_value, True))

        return EditRow(self.row_id, edit_cells, EditRowState.DIRTY_INSERT)

    def get_script(self) -> EditScript:
        return self._generate_insert_script()

    def apply_changes(self):
        edit_row = self.get_edit_row([])
        cell_values = [cell.display_value for cell in edit_row.cells]

        self.result_set.add_row(tuple(cell_values))

    def _generate_insert_script(self):

        insert_template = 'INSERT INTO {0}({1}) VALUES(%s)'

        column_names: List[str] = []
        query_parameters: List[object] = []

        for index, column in enumerate(self.result_set.columns):
            if column.is_updatable is True:
                column_names.append(column.column_name)

                cell_update = self.new_cells[index]
                query_parameters.append(cell_update.value)

        query_template = str.format(insert_template, self.table_metadata.escaped_multipart_name, ', '.join(column_names))

        return EditScript(query_template, query_parameters)
