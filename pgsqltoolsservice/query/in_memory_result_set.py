# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List

from pgsqltoolsservice.query.result_set import ResultSet, ResultSetEvents
from pgsqltoolsservice.query_execution.contracts.common import ResultSetSubset
from pgsqltoolsservice.query_execution.contracts.common import DbColumn, DbCellValue # noqa


class InMemoryResultSet(ResultSet):

    def __init__(self, result_set_id: int, batch_id: int, events: ResultSetEvents = None) -> None:
        ResultSet.__init__(self, result_set_id, batch_id, events)
        self.rows: List[tuple] = []

    @property
    def row_count(self) -> int:
        return len(self.rows)

    def get_subset(self, start_index: int, end_index: int):
        return ResultSetSubset.from_result_set(self, start_index, end_index)

    def add_row(self, cursor):
        self.rows.append(cursor.fetchone())

    def remove_row(self, row_id: int):
        del self.rows[row_id]

    def update_row(self, row_id: int, cursor):
        self.rows[row_id] = cursor.fetchone()

    def get_row(self, row_id: int) -> List[DbCellValue]:
        row = self.rows[row_id]
        return [DbCellValue(cell_value, cell_value is None, cell_value, row_id) for cell_value in list(row)]

    def read_result_to_end(self, cursor):
        rows = cursor.fetchall()
        self.rows.extend(rows)
