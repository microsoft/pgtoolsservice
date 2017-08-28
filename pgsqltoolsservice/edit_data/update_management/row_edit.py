# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List # noqa
from abc import abstractmethod

from pgsqltoolsservice.query_execution.result_set import ResultSet
from pgsqltoolsservice.edit_data import EditTableMetadata
from pgsqltoolsservice.query_execution.contracts.common import DbCellValue
from pgsqltoolsservice.edit_data.contracts import EditCellResponse


class RowEdit:

    def __init__(self, row_id, result_set: ResultSet, table_metadata: EditTableMetadata):
        self.row_id = row_id
        self.result_set = result_set
        self.table_metadata = table_metadata
        self.row = self._get_db_cell_values_for_row()

    @abstractmethod
    def set_cell_value(self, column_index: int, new_value: str) -> EditCellResponse:
        pass

    @abstractmethod
    def get_edit_row(self, cached_row: List[DbCellValue]):
        pass

    @abstractmethod
    def get_script(self):
        pass

    @abstractmethod
    def revert_cell_value(self, column_index: int):
        pass

    def _get_db_cell_values_for_row(self)-> List[DbCellValue]:

        row = self.result_set.rows[self.row_id]
        return [DbCellValue(cell_value, cell_value is None, cell_value, self.row_id) for cell_value in list(row)]
