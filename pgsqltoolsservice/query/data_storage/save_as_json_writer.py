# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import json
from typing import List

from pgsqltoolsservice.query.data_storage.save_as_writer import SaveAsWriter
from pgsqltoolsservice.query.contracts import DbColumn, DbCellValue, SaveResultsRequestParams


class SaveAsJsonWriter(SaveAsWriter):

    def __init__(self, stream: io.BufferedWriter, params: SaveResultsRequestParams) -> None:
        SaveAsWriter.__init__(self, stream, params)

        self._data = []

    def write_row(self, row: List[DbCellValue], columns: List[DbColumn]):

        column_start_index = self.get_start_index()
        column_end_index = self.get_end_index(columns)

        json_row = {}

        for index in range(column_start_index, column_end_index):
            column_name = columns[index].column_name
            column_value = row[index].display_value
            json_row[column_name] = column_value

        self._data.append(json_row)

    def complete_write(self):
        json.dump(self._data, self._file_stream, indent=True)
