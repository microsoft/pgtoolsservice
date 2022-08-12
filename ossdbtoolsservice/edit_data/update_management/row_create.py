# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import List

from ossdbtoolsservice.edit_data import EditTableMetadata
from ossdbtoolsservice.edit_data.contracts import (EditCell, EditCellResponse,
                                                   EditRow, EditRowState,
                                                   RevertCellResponse)
from ossdbtoolsservice.edit_data.update_management import (CellUpdate,
                                                           EditScript, RowEdit)
from ossdbtoolsservice.query import ResultSet
from ossdbtoolsservice.query.contracts import DbCellValue
from ossdbtoolsservice.utils.constants import MYSQL_PROVIDER_NAME


class RowCreate(RowEdit):

    def __init__(self, row_id: int, result_set: ResultSet, table_metadata: EditTableMetadata):
        super(RowCreate, self).__init__(row_id, result_set, table_metadata)
        self.new_cells: List[CellUpdate] = [None] * len(result_set.columns_info)
        if table_metadata._provider_name == MYSQL_PROVIDER_NAME:
            self.supports_returning = False

    def set_cell_value(self, column_index: int, new_value: str) -> EditCellResponse:

        self.validate_column_is_updatable(column_index)

        cell_update = CellUpdate(self.result_set.columns_info[column_index], new_value, self.table_metadata._provider_name)
        self.new_cells[column_index] = cell_update

        return EditCellResponse(cell_update.as_edit_cell, True)

    def revert_cell_value(self, column_index: int) -> RevertCellResponse:
        self.new_cells[column_index] = None
        return RevertCellResponse(None, True)

    def get_edit_row(self, cached_row: List[DbCellValue]) -> EditRow:

        edit_cells = []
        for cell in self.new_cells:
            db_cell_value = DbCellValue(None, True, None, self.row_id) if cell is None else cell.as_db_cell_value
            edit_cells.append(EditCell(db_cell_value, True, self.row_id))

        return EditRow(self.row_id, edit_cells, EditRowState.DIRTY_INSERT)

    def get_script(self) -> EditScript:
        return self._generate_insert_script()

    def apply_changes(self, cursor):
        self.result_set.add_row(cursor)

    def _generate_insert_script(self):

        insert_template = self.templater.insert_template
        colum_name_template = self.templater.object_template

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

                insert_values.append('%s')

        query_template = str.format(insert_template, self.table_metadata.multipart_name, ', '.join(column_names), ', '.join(insert_values))

        return EditScript(query_template, query_parameters)

    def get_returning_script(self) -> EditScript:
        return self._generate_select_script()

    def _generate_select_script(self):
        select_template = self.templater.select_template
        object_name_template = self.templater.object_template
        column_name_template = self.templater.column_name_template
        where_start = self.templater.where_template

        column_names: List[str] = []
        where_clauses: List[str] = []
        query_parameters: List[object] = []

        for index, column in enumerate(self.result_set.columns_info):
            if column.is_updatable is True:
                column_names.append(str.format(object_name_template, column.column_name))
                where_clauses.append(column_name_template.format( column.column_name, '= %s'))

                cell_update = self.new_cells[index]
                if cell_update is None:  # It is none when a column is not updated
                    query_parameters.append(None)
                else:
                    query_parameters.append(cell_update.value)

        where_template = where_start.format(' AND '.join(where_clauses))
        query_template = str.format(select_template, self.table_metadata.multipart_name, where_template)

        return EditScript(query_template, query_parameters)
