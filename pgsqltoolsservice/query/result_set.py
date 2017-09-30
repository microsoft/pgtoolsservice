# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABCMeta, abstractmethod, abstractproperty
from typing import List  # noqa

from pgsqltoolsservice.query.contracts import DbColumn, DbCellValue, ResultSetSummary # noqa


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
