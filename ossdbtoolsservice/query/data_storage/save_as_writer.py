# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
from abc import abstractmethod
from typing import Any, Generic, TypeVar

from ossdbtoolsservice.query.contracts import DbCellValue, DbColumn
from ossdbtoolsservice.query.contracts.save_as_request import SaveResultsRequestParams
from ossdbtoolsservice.query.data_storage.service_buffer import ServiceBufferFileStream

T = TypeVar("T", bound="SaveResultsRequestParams")


class SaveAsWriter(ServiceBufferFileStream, Generic[T]):
    def __init__(self, stream: io.BufferedWriter | io.TextIOWrapper, params: T) -> None:
        self._file_stream = stream

        self._params = params
        self._column_start_index: int | None = (
            params.column_start_index if params.is_save_selection else None
        )
        self._column_end_index: int | None = (
            params.column_end_index if params.is_save_selection else None
        )
        self._column_count: int | None = (
            params.column_end_index - params.column_start_index + 1
            if params.is_save_selection
            and params.column_start_index is not None
            and params.column_end_index is not None
            else None
        )

    def __enter__(self) -> "SaveAsWriter":
        return self

    def __exit__(self, *args: Any) -> None:
        self._file_stream.close()

    @abstractmethod
    def write_row(self, row: list[DbCellValue], columns: list[DbColumn]) -> None:
        pass

    @abstractmethod
    def complete_write(self) -> None:
        pass

    def get_start_index(self) -> int:
        return self._column_start_index if self._column_start_index else 0

    def get_end_index(self, columns: list[DbColumn]) -> int:
        return self._column_count if self._column_count else len(columns)
