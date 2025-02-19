# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import csv
import io
from typing import TYPE_CHECKING

from ossdbtoolsservice.query.contracts import DbCellValue, DbColumn
from ossdbtoolsservice.query.data_storage.save_as_writer import SaveAsWriter

if TYPE_CHECKING:
    from ossdbtoolsservice.query_execution.contracts.save_result_as_request import (
        SaveResultsAsCsvRequestParams,
    )


class SaveAsCsvWriter(SaveAsWriter):
    def __init__(
        self,
        stream: io.BufferedWriter | io.TextIOWrapper,
        params: "SaveResultsAsCsvRequestParams",
    ) -> None:
        SaveAsWriter.__init__(self, stream, params)
        self._params = params
        self._header_written = False

    def write_row(self, row: list[DbCellValue], columns: list[DbColumn]) -> None:
        writer = csv.writer(
            self._file_stream,  # type: ignore
            delimiter=self._params.delimiter,
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
            lineterminator="\n",
        )

        if self._params.include_headers and not self._header_written:
            selected_column_names = [
                column.column_name
                for column in columns[self.get_start_index() : self.get_end_index(columns)]
            ]
            writer.writerow(selected_column_names)

            self._header_written = True

        selected_cells = [
            cell.display_value
            for cell in row[self.get_start_index() : self.get_end_index(columns)]
        ]

        writer.writerow(selected_cells)

    def complete_write(self) -> None:
        pass
