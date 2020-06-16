# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
from typing import List
import xlsxwriter
import string

from ostoolsservice.query.data_storage.save_as_writer import SaveAsWriter
from ostoolsservice.query.contracts import DbColumn, DbCellValue, SaveResultsRequestParams


class SaveAsExcelWriter(SaveAsWriter):

    def __init__(self, stream: io.BufferedWriter, params: SaveResultsRequestParams) -> None:
        SaveAsWriter.__init__(self, stream, params)

        self._header_written = False
        self._workbook = xlsxwriter.Workbook(self._file_stream.name)
        self._worksheet = self._workbook.add_worksheet()
        self._current_row = 1

    def write_row(self, row: List[DbCellValue], columns: List[DbColumn]):

        column_start_index = self.get_start_index()
        column_end_index = self.get_end_index(columns)

        if not self._header_written:
            bold = self._workbook.add_format({'bold': 1})
            for index, column in enumerate(columns[column_start_index: column_end_index]):
                self._worksheet.write(string.ascii_uppercase[index] + '1', column.column_name, bold)

            self._header_written = True

        for loop_index, column_index in enumerate(range(column_start_index, column_end_index)):
            self._worksheet.write(self._current_row, loop_index, row[column_index].display_value)

        self._current_row += 1

    def complete_write(self):
        self._workbook.close()
