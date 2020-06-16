# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import csv
from typing import List

from ostoolsservice.query.data_storage.save_as_writer import SaveAsWriter
from ostoolsservice.query.contracts import DbColumn, DbCellValue, SaveResultsRequestParams


class SaveAsCsvWriter(SaveAsWriter):

    def __init__(self, stream: io.BufferedWriter, params: SaveResultsRequestParams) -> None:
        SaveAsWriter.__init__(self, stream, params)
        self._header_written = False

    def write_row(self, row: List[DbCellValue], columns: List[DbColumn]):

        writer = csv.writer(self._file_stream, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        if self._params.include_headers and not self._header_written:
            selected_column_names = [column.column_name for column in columns[
                self.get_start_index(): self.get_end_index(columns)]]
            writer.writerow(selected_column_names)

            self._header_written = True

        selected_cells = [cell.display_value for cell in row[
            self.get_start_index(): self.get_end_index(columns)]]

        writer.writerow(selected_cells)
