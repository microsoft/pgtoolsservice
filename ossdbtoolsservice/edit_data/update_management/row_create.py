# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import List

from ossdbtoolsservice.edit_data import EditTableMetadata
from ossdbtoolsservice.edit_data.contracts import (
    EditCell,
    EditCellResponse,
    EditRow,
    EditRowState,
    RevertCellResponse,
)
from ossdbtoolsservice.edit_data.update_management import CellUpdate, EditScript, RowEdit
from ossdbtoolsservice.query import ResultSet
from ossdbtoolsservice.query.contracts import DbCellValue


class RowCreate(RowEdit):
    def __init__(self, row_id: int, result_set: ResultSet, table_metadata: EditTableMetadata):
        super(RowCreate, self).__init__(row_id, result_set, table_metadata)
        self.new_cells: List[CellUpdate] = [None] * len(result_set.columns_info)

    def set_cell_value(self, column_index: int, new_value: str) -> EditCellResponse:
        self.validate_column_is_updatable(column_index)

        cell_update = CellUpdate(self.result_set.columns_info[column_index], new_value)
        self.new_cells[column_index] = cell_update

        return EditCellResponse(cell_update.as_edit_cell, True)

    def revert_cell_value(self, column_index: int) -> RevertCellResponse:
        self.new_cells[column_index] = None
        return RevertCellResponse(None, True)

    def get_edit_row(self, cached_row: List[DbCellValue]) -> EditRow:
        edit_cells = []
        for cell in self.new_cells:
            db_cell_value = (
                DbCellValue(None, True, None, self.row_id)
                if cell is None
                else cell.as_db_cell_value
            )
            edit_cells.append(EditCell(db_cell_value, True, self.row_id))

        return EditRow(self.row_id, edit_cells, EditRowState.DIRTY_INSERT)

    def get_script(self) -> EditScript:
        return self._generate_insert_script()

    def apply_changes(self, cursor):
        self.result_set.add_row(cursor)

    def _generate_insert_script(self):
        insert_template = "INSERT INTO {0}({1}) VALUES({2}) RETURNING *"
        colum_name_template = '"{0}"'

        column_names: List[str] = []
        query_parameters: List[object] = []
        insert_values: List[str] = []

        for index, column in enumerate(self.result_set.columns_info):
            if column.is_updatable is True:
                column_names.append(str.format(colum_name_template, column.column_name))

                cell_update = self.new_cells[index]

                if cell_update is None:  # It is none when a column is not updated
                    query_parameters.append(None)
                else:
                    query_parameters.append(cell_update.value)

                insert_values.append("%s")

        query_template = str.format(
            insert_template,
            self.table_metadata.multipart_name,
            ", ".join(column_names),
            ", ".join(insert_values),
        )

        return EditScript(query_template, query_parameters)
