# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Dict, List  # noqa

from ossdbtoolsservice.edit_data import EditTableMetadata
from ossdbtoolsservice.edit_data.contracts import (EditCell, EditCellResponse,
                                                   EditRow, EditRowState,
                                                   RevertCellResponse)
from ossdbtoolsservice.edit_data.update_management import (CellUpdate,
                                                           EditScript, RowEdit)
from ossdbtoolsservice.query import ResultSet
from ossdbtoolsservice.query.contracts import DbCellValue
from ossdbtoolsservice.utils.constants import MYSQL_PROVIDER_NAME

class RowUpdate(RowEdit):

    def __init__(self, row_id: int, result_set: ResultSet, table_metadata: EditTableMetadata):
        super(RowUpdate, self).__init__(row_id, result_set, table_metadata)
        self.row = result_set.get_row(row_id)
        self._cell_updates: Dict[int, CellUpdate] = {}
        # if MySQL connection, then will need to run a SELECT statement after UPDATE
        # in order to grab data for in-memory table
        if table_metadata._provider_name == MYSQL_PROVIDER_NAME:
            self.supports_returning = False

    def set_cell_value(self, column_index: int, new_value: str) -> EditCellResponse:
        self.validate_column_is_updatable(column_index)
        cell_update = CellUpdate(self.result_set.columns_info[column_index], new_value, self.table_metadata._provider_name)

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

        query = self.templater.update_template
        set_template = self.templater.set_template

        set_query = []
        cell_values = []
        for cell in self._cell_updates.values():
            cell_values.append(cell.value)
            set_query.append(set_template.format(cell.column.column_name))

        set_join = ', '.join(set_query)

        where_script = self.build_where_clause()
        query_template = query.format(self.table_metadata.multipart_name, set_join, where_script.query_template)
        cell_values.extend(where_script.query_parameters)

        return EditScript(query_template, cell_values)

    def get_returning_script(self) -> EditScript:
        cell_values = []
        where_script = self.build_where_clause()

        # if any of the key columns were changed, add the new value 
        # instead of the where script parameter, because we just updated a key
        key_columns = [column.db_column for column in self.table_metadata.key_columns]
        updated_columns = [value.column for value in self._cell_updates.values()]
        for i, column in enumerate(key_columns):
            if column in updated_columns:
                cell_values.append(self._cell_updates[column.column_ordinal].value)
            else:
                cell_values.append(where_script.query_parameters[i])
                
        query_template = self.templater.select_template.format(self.table_metadata.multipart_name, where_script.query_template)
        return EditScript(query_template, cell_values)

    def apply_changes(self, cursor):
        self.result_set.update_row(self.row_id, cursor)
