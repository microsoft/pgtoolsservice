# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List

from ossdbtoolsservice.edit_data import EditTableMetadata
from ossdbtoolsservice.edit_data.contracts import (EditCell, EditCellResponse,
                                                   EditRow, EditRowState,
                                                   RevertCellResponse)
from ossdbtoolsservice.edit_data.update_management import EditScript, RowEdit
from ossdbtoolsservice.query import ResultSet
from ossdbtoolsservice.query.contracts import DbCellValue


class RowDelete(RowEdit):

    def __init__(self, row_id: int, result_set: ResultSet, table_metadata: EditTableMetadata) -> None:
        super(RowDelete, self).__init__(row_id, result_set, table_metadata)

    def revert_cell_value(self, column_index: int) -> RevertCellResponse:
        raise TypeError('Revert cell not supported')

    def set_cell_value(self, column_index: int, new_value: str) -> EditCellResponse:
        raise TypeError('Set cell not supported')

    def get_edit_row(self, cached_row: List[DbCellValue]) -> EditRow:
        return EditRow(self.row_id, [EditCell(cell, True, self.row_id) for cell in cached_row], EditRowState.DIRTY_DELETE)

    def apply_changes(self, cursor):
        self.result_set.remove_row(self.row_id)

    def get_script(self) -> EditScript:
        where_script = self.build_where_clause()
        delete_script = self.templater.delete_template

        query_template = delete_script.format(self.table_metadata.multipart_name, where_script.query_template)

        return EditScript(query_template, where_script.query_parameters)
