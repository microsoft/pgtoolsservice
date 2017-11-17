# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABCMeta, abstractmethod, abstractproperty
from typing import List, Dict  # noqa
import threading

from pgsqltoolsservice.query.contracts import DbColumn, DbCellValue, ResultSetSummary, SaveResultsRequestParams  # noqa
from pgsqltoolsservice.query.data_storage import FileStreamFactory


class ResultSetEvents:

    def __init__(self, on_result_set_completed=None, on_result_set_partially_loaded=None) -> None:
        self._on_result_set_completed = on_result_set_completed
        self._on_result_set_partially_loaded = on_result_set_partially_loaded


class ResultSet(metaclass=ABCMeta):

    def __init__(self, result_set_id: int, batch_id: int, events: ResultSetEvents = None) -> None:
        self.id = result_set_id
        self.batch_id = batch_id
        self.events = events

        self._has_been_read = False
        self._columns_info: List[DbColumn] = []
        self._save_as_threads: Dict[str, threading.Thread] = {}

    @property
    def columns_info(self) -> List[DbColumn]:
        return self._columns_info if self._columns_info is not None else []

    @columns_info.setter
    def columns_info(self, columns_info) -> None:
        self._columns_info = columns_info

    @property
    def result_set_summary(self) -> ResultSetSummary:
        return ResultSetSummary(self.id, self.batch_id, self.row_count, self.columns_info)

    @abstractproperty
    def row_count(self) -> int:
        pass

    @abstractmethod
    def get_subset(self, start_index: int, end_index: int):
        pass

    @abstractmethod
    def add_row(self, cursor):
        ''' Add row accepts cursor which will be iterated over to get the current row to add '''
        pass

    @abstractmethod
    def remove_row(self, row_id: int):
        pass

    @abstractmethod
    def update_row(self, row_id: int, cursor):
        ''' Add row accepts cursor which will be iterated over to get the current row to be updated '''
        pass

    @abstractmethod
    def get_row(self, row_id: int) -> List[DbCellValue]:
        pass

    @abstractmethod
    def read_result_to_end(self, cursor):
        pass

    @abstractmethod
    def do_save_as(self, file_path: str, row_start_index: int, row_end_index: int, file_factory: FileStreamFactory, on_success, on_failure) -> None:
        pass

    def save_as(self, params: SaveResultsRequestParams, file_factory: FileStreamFactory, on_success, on_failure) -> None:

        if self._has_been_read is False:
            raise RuntimeError('Result cannot be saved until query execution has completed')

        save_as_thread = self._save_as_threads.get(params.file_path)

        if save_as_thread is not None:
            if save_as_thread.isAlive():
                raise RuntimeError('A save request to the same path is in progress')
            else:
                del self._save_as_threads[params.file_path]

        row_end_index = self.row_count
        row_start_index = 0

        if params.is_save_selection:
            row_end_index = params.row_end_index + 1
            row_start_index = params.row_start_index

        new_save_as_thread = threading.Thread(
            target=self.do_save_as,
            args=(params.file_path, row_start_index, row_end_index, file_factory, on_success, on_failure),
            daemon=True)
        self._save_as_threads[params.file_path] = new_save_as_thread
        new_save_as_thread.start()
