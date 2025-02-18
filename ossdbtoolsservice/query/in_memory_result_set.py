# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.query.column_info import get_columns_info
from ossdbtoolsservice.query.contracts import (  # noqa
    DbCellValue,
    DbColumn,
    ResultSetSubset,
    SaveResultsRequestParams,
)
from ossdbtoolsservice.query.data_storage import FileStreamFactory
from ossdbtoolsservice.query.result_set import ResultSet, ResultSetEvents


class InMemoryResultSet(ResultSet):
    def __init__(
        self, result_set_id: int, batch_id: int, events: ResultSetEvents = None
    ) -> None:
        ResultSet.__init__(self, result_set_id, batch_id, events)
        self.rows: list[tuple] = []

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

    def get_row(self, row_id: int) -> list[DbCellValue]:
        row = self.rows[row_id]
        return [
            DbCellValue(cell_value, cell_value is None, cell_value, row_id)
            for cell_value in list(row)
        ]

    def read_result_to_end(self, cursor):
        rows = cursor.fetchall()
        self.rows.extend(rows or [])

        self.columns_info = get_columns_info(cursor)

        self._has_been_read = True

    def do_save_as(
        self,
        file_path: str,
        row_start_index: int,
        row_end_index: int,
        file_factory: FileStreamFactory,
        on_success,
        on_failure,
    ) -> None:
        with file_factory.get_writer(file_path) as writer:
            for index in range(row_start_index, row_end_index):
                row = self.get_row(index)
                writer.write_row(row, self.columns_info)

            writer.complete_write()

            if on_success is not None:
                on_success()
