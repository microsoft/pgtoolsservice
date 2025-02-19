# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import Any

import psycopg

from ossdbtoolsservice.query.column_info import get_columns_info
from ossdbtoolsservice.query.contracts import DbColumn


class StorageDataReader:
    def __init__(self, cursor: psycopg.Cursor) -> None:
        self._cursor = cursor
        self._current_row: tuple | None = None
        self._columns_info: list[DbColumn] = []

    @property
    def columns_info(self) -> list[DbColumn]:
        return self._columns_info

    def read_row(self) -> bool:
        """
        read_row uses the cursor to iterate over. It iterates over the cursor one at a time
        and returns True if it finds the row and False if it doesn’t
        """
        row_found = False

        for row in self._cursor:
            self._current_row = row
            row_found = True
            break

        if self._current_row is None or len(self._columns_info) == 0:
            self._columns_info = get_columns_info(self._cursor)

        return row_found

    def get_value(self, column_index: int) -> Any:
        if self._current_row is None:
            raise ValueError("Result set not read")
        return self._current_row[column_index]

    def get_values(self) -> tuple:
        if self._current_row is None:
            raise ValueError("Result set not read")
        return self._current_row

    def is_none(self, column_index: int) -> bool:
        if self._current_row is None:
            raise ValueError("Result set not read")
        return self._current_row[column_index] is None

    def get_bytes_with_max_capacity(
        self, column_index: int, max_bytes_to_return: int
    ) -> bytearray:
        if max_bytes_to_return <= 0:
            raise ValueError("Maximum number of bytes to return must be greater than zero")
        if self._current_row is None:
            raise ValueError("Result set not read")

        column_value = self._current_row[column_index]

        if isinstance(column_value, (bytes, bytearray, memoryview)):
            return bytearray(column_value)[0:max_bytes_to_return]
        else:
            raise ValueError("Not a bytes column")

    def get_chars_with_max_capacity(self, column_index: int, max_chars_to_return: int) -> str:
        if max_chars_to_return <= 0:
            raise ValueError("Maximum number of chars to return must be greater than zero")
        if self._current_row is None:
            raise ValueError("Result set not read")

        column_value = self._current_row[column_index]

        if isinstance(column_value, str):
            return column_value[0:max_chars_to_return]
        else:
            raise ValueError("Not a str column")

    def get_xml_with_max_capacity(self, column_index: int, max_chars_to_return: int) -> str:
        if max_chars_to_return <= 0:
            raise ValueError(
                "Maximum number of XML bytes to return must be greater than zero"
            )
        if self._current_row is None:
            raise ValueError("Result set not read")

        column_value = self._current_row[column_index]

        return column_value[0:max_chars_to_return]
