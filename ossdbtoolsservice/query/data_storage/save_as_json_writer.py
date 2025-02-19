# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import json
from typing import Any

from ossdbtoolsservice.query.contracts import DbCellValue, DbColumn, SaveResultsRequestParams
from ossdbtoolsservice.query.data_storage.save_as_writer import SaveAsWriter


class SaveAsJsonWriter(SaveAsWriter):
    def __init__(
        self, stream: io.BufferedWriter | io.TextIOWrapper, params: SaveResultsRequestParams
    ) -> None:
        SaveAsWriter.__init__(self, stream, params)

        self._data: list[dict[str, Any]] = []

    def write_row(self, row: list[DbCellValue], columns: list[DbColumn]) -> None:
        column_start_index = self.get_start_index()
        column_end_index = self.get_end_index(columns)

        json_row: dict[str, str] = {}

        for index in range(column_start_index, column_end_index):
            column_name = columns[index].column_name or str(index)
            column_value: Any = row[index].raw_object
            if not is_json_serializable_type(column_value):
                column_value = row[index].display_value

            json_row[column_name] = column_value

        self._data.append(json_row)

    def complete_write(self) -> None:
        json.dump(
            self._data,
            self._file_stream,  # type: ignore
            indent=True,
        )


def is_json_serializable_type(value: Any) -> bool:
    json_serializable_types = (str, int, float, bool, type(None), list, dict)
    return isinstance(value, json_serializable_types)
