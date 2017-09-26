# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
from typing import List  # noqa
from datetime import datetime

import psycopg2
import uuid
import sqlparse

from pgsqltoolsservice.utils.time import get_time_str, get_elapsed_time_str
from pgsqltoolsservice.query_execution.contracts.common import SelectionData
from pgsqltoolsservice.query.result_set import ResultSet # noqa
from pgsqltoolsservice.query.contracts import BatchSummary
from pgsqltoolsservice.query.file_storage_result_set import FileStorageResultSet
from pgsqltoolsservice.query.in_memory_result_set import InMemoryResultSet


class ResultSetStorageType(Enum):
    IN_MEMORY = 1,
    FILE_STORAGE = 2


class BatchEvents:

    def __init__(self, on_execution_started=None, on_execution_completed=None, on_result_set_completed=None):
        self._on_execution_started = on_execution_started
        self._on_execution_completed = on_execution_completed
        self._on_result_set_completed = on_result_set_completed


class SelectBatchEvents(BatchEvents):

    def __init__(self, on_execution_started, on_execution_completed, on_result_set_completed, on_after_first_fetch):
        BatchEvents.__init__(self, on_execution_started, on_execution_completed, on_result_set_completed)
        self._on_after_first_fetch = on_after_first_fetch


class Batch:

    def __init__(self, batch_text: str, ordinal: int, selection: SelectionData, batch_events: BatchEvents, storage_type: ResultSetStorageType) -> None:
        self.id = ordinal
        self.selection = selection
        self.batch_text = batch_text

        self._execution_start_time: datetime = None
        self._has_error = False
        self._has_executed = False
        self._execution_end_time: datetime = None
        self._result_set: ResultSet = None
        self._notices: List[str] = []
        self._batch_events = batch_events
        self._storage_type = storage_type

    @property
    def batch_summary(self) -> BatchSummary:
        return BatchSummary.from_batch(self)

    @property
    def has_error(self) -> bool:
        return self._has_error

    @property
    def has_executed(self) -> bool:
        return self._has_executed

    @property
    def start_time(self) -> str:
        return get_time_str(self._execution_start_time)

    @property
    def end_time(self) -> str:
        return get_time_str(self._execution_end_time)

    @property
    def elapsed_time(self) -> str:
        return get_elapsed_time_str(self._execution_start_time, self._execution_end_time)

    @property
    def result_set(self) -> ResultSet:
        return self._result_set

    @property
    def notices(self) -> List[str]:
        return self._notices

    def get_cursor(self, connection: 'psycopg2.extensions.connection'):
        return connection.cursor()

    def execute(self, connection: 'psycopg2.extensions.connection') -> None:
        """
        Execute the batch using the psycopg2 cursor retrieved from the given connection

        :raises psycopg2.DatabaseError: if an error is encountered while running the batch's query
        """
        try:
            cursor = self.get_cursor(connection)
            self._execution_start_time = datetime.now()
            cursor.execute(self.batch_text)
        except psycopg2.DatabaseError:
            self._has_error = True
            raise
        finally:
            self._has_executed = True
            self._execution_end_time = datetime.now()
            self._notices = cursor.connection.notices
            cursor.connection.notices = []

        if cursor.description is not None:
            result_set = create_result_set(self._storage_type, 0, self.id)
            result_set.read_result_to_end(cursor)
            self._result_set = result_set


class SelectBatch(Batch):

    def __init__(self, batch_text: str, ordinal: int, selection: SelectionData, batch_events: SelectBatchEvents, storage_type: ResultSetStorageType) -> None:
        Batch.__init__(self, batch_text, ordinal, selection, batch_events, storage_type)

    def get_cursor(self, connection: 'psycopg2.extensions.connection'):
        cursor_name = str(uuid.uuid4())
        return connection.cursor(cursor_name)


def create_result_set(storage_type: ResultSetStorageType, result_set_id: int, batch_id: int) -> ResultSet:

    if storage_type is ResultSetStorageType.FILE_STORAGE:
        return FileStorageResultSet(result_set_id, batch_id)

    return InMemoryResultSet(result_set_id, batch_id)


def create_batch(batch_text: str, ordinal: int, selection: SelectionData, batch_events: BatchEvents, storage_type: ResultSetStorageType) -> Batch:
    sql = sqlparse.parse(batch_text)
    statement = sql[0]

    if statement.get_type().lower() == 'select':
        index = statement.token_index(statement.token_first())
        second_token = statement.token_next(index)

        if second_token[1].value.lower() != 'into':
            return SelectBatch(batch_text, ordinal, selection, batch_events, storage_type)

    return Batch(batch_text, ordinal, selection, batch_events, storage_type)
