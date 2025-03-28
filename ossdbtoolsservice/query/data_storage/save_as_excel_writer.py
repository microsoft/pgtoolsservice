# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io

import xlsxwriter

from ossdbtoolsservice.query.contracts import DbCellValue, DbColumn, SaveResultsRequestParams
from ossdbtoolsservice.query.data_storage.save_as_writer import SaveAsWriter


class SaveAsExcelWriter(SaveAsWriter):
    def __init__(
        self, stream: io.BufferedWriter | io.TextIOWrapper, params: SaveResultsRequestParams
    ) -> None:
        SaveAsWriter.__init__(self, stream, params)

        self._header_written = False
        self._workbook = xlsxwriter.Workbook(stream.name)
        self._worksheet = self._workbook.add_worksheet()
        self._current_row = 1

    def write_row(self, row: list[DbCellValue], columns: list[DbColumn]) -> None:
        column_start_index = self.get_start_index()
        column_end_index = self.get_end_index(columns)

        if not self._header_written:
            bold = self._workbook.add_format({"bold": 1})
            for index, column in enumerate(columns[column_start_index:column_end_index]):
                self._worksheet.write(0, index, column.column_name, bold)

            self._header_written = True

        for loop_index, column_index in enumerate(
            range(column_start_index, column_end_index)
        ):
            self._worksheet.write(self._current_row, loop_index, row[column_index].raw_object)

        self._current_row += 1

    def complete_write(self) -> None:
        self._workbook.close()
