# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading
from abc import ABCMeta, abstractmethod
from typing import Callable

import psycopg

from ossdbtoolsservice.query.contracts import (
    DbCellValue,
    DbColumn,
    ResultSetSummary,
    SaveResultsRequestParams,
)
from ossdbtoolsservice.query.contracts.result_set_subset import ResultSetSubset
from ossdbtoolsservice.query.data_storage import FileStreamFactory


# This class seems unused.
class ResultSetEvents:
    def __init__(
        self,
        on_result_set_completed: Callable | None = None,
        on_result_set_partially_loaded: Callable | None = None,
    ) -> None:
        self._on_result_set_completed = on_result_set_completed
        self._on_result_set_partially_loaded = on_result_set_partially_loaded


class ResultSet(metaclass=ABCMeta):
    def __init__(
        self, result_set_id: int, batch_id: int, events: ResultSetEvents | None = None
    ) -> None:
        self.id = result_set_id
        self.batch_id = batch_id
        self.events = events

        self._has_been_read = False
        self._columns_info: list[DbColumn] = []
        self._save_as_threads: dict[str, threading.Thread] = {}

    @property
    def columns_info(self) -> list[DbColumn]:
        return self._columns_info if self._columns_info is not None else []

    @columns_info.setter
    def columns_info(self, columns_info: list[DbColumn]) -> None:
        self._columns_info = columns_info

    @property
    def result_set_summary(self) -> ResultSetSummary:
        return ResultSetSummary(
            id=self.id,
            batch_id=self.batch_id,
            row_count=self.row_count,
            complete=self._has_been_read,
            column_info=self.columns_info,
        )

    @property
    @abstractmethod
    def row_count(self) -> int:
        pass

    @abstractmethod
    def get_subset(self, start_index: int, end_index: int) -> ResultSetSubset:
        pass

    @abstractmethod
    def add_row(self, cursor: psycopg.Cursor) -> None:
        """Add row accepts cursor which will be iterated over to get the current row to add"""
        pass

    @abstractmethod
    def remove_row(self, row_id: int) -> None:
        pass

    @abstractmethod
    def update_row(self, row_id: int, cursor: psycopg.Cursor) -> None:
        """Add row accepts cursor which will be iterated over
        to get the current row to be updated"""
        pass

    @abstractmethod
    def get_row(self, row_id: int) -> list[DbCellValue]:
        pass

    @abstractmethod
    def read_result_to_end(self, cursor: psycopg.Cursor) -> None:
        pass

    @abstractmethod
    def do_save_as(
        self,
        file_path: str,
        row_start_index: int,
        row_end_index: int,
        file_factory: FileStreamFactory,
        on_success: Callable[[], None],
        on_failure: Callable[[Exception], None],
    ) -> None:
        pass

    def save_as(
        self,
        params: SaveResultsRequestParams,
        file_factory: FileStreamFactory,
        on_success: Callable[[], None],
        on_failure: Callable[[Exception], None],
    ) -> None:
        if self._has_been_read is False:
            raise RuntimeError("Result cannot be saved until query execution has completed")

        file_path = params.file_path
        if file_path is None:
            raise ValueError("File path cannot be None")

        # Validate is_save_selection
        row_end_index = self.row_count
        row_start_index = 0

        if params.is_save_selection:
            if params.row_start_index is None or params.row_end_index is None:
                raise ValueError("Row start and end indexes cannot be None")
            if params.row_start_index < 0 or params.row_end_index < 0:
                raise ValueError("Row start and end indexes must be non-negative")
            if params.row_start_index > params.row_end_index:
                raise ValueError("Row start index cannot be greater than row end index")

            row_end_index = params.row_end_index + 1
            row_start_index = params.row_start_index

        save_as_thread = self._save_as_threads.get(file_path)

        if save_as_thread is not None:
            if save_as_thread.is_alive():
                raise RuntimeError("A save request to the same path is in progress")
            else:
                del self._save_as_threads[file_path]

        new_save_as_thread = threading.Thread(
            target=self.do_save_as,
            args=(
                params.file_path,
                row_start_index,
                row_end_index,
                file_factory,
                on_success,
                on_failure,
            ),
            daemon=True,
        )
        self._save_as_threads[file_path] = new_save_as_thread
        new_save_as_thread.start()
