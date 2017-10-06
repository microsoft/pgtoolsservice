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
from pgsqltoolsservice.query.contracts import BatchSummary, SelectionData
from pgsqltoolsservice.query.result_set import ResultSet  # noqa
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

    def __init__(
            self,
            batch_text: str,
            ordinal: int,
            selection: SelectionData,
            batch_events: BatchEvents= None,
            storage_type: ResultSetStorageType= ResultSetStorageType.IN_MEMORY
    ) -> None:
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
    def row_count(self) -> int:
        return self.result_set.row_count if self.result_set is not None else -1

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
        self._execution_start_time = datetime.now()

        if self._batch_events and self._batch_events._on_execution_started:
            self._batch_events._on_execution_started(self)

        try:
            cursor = self.get_cursor(connection)
            cursor.execute(self.batch_text)

            self.after_execute(cursor)
        except psycopg2.DatabaseError:
            self._has_error = True
            raise
        finally:
            cursor.close()
            self._has_executed = True
            self._execution_end_time = datetime.now()
            self._notices = cursor.connection.notices

            cursor.connection.notices = []

            if self._batch_events and self._batch_events._on_execution_completed:
                self._batch_events._on_execution_completed(self)

    def after_execute(self, cursor) -> None:
        if cursor.description is not None:
            self.create_result_set(cursor)

    def create_result_set(self, cursor):
        result_set = create_result_set(self._storage_type, 0, self.id)
        result_set.read_result_to_end(cursor)
        self._result_set = result_set

    def get_subset(self, start_index: int, end_index: int):
        return self._result_set.get_subset(start_index, end_index)


class SelectBatch(Batch):

    def __init__(self, batch_text: str, ordinal: int, selection: SelectionData, batch_events: SelectBatchEvents, storage_type: ResultSetStorageType) -> None:
        Batch.__init__(self, batch_text, ordinal, selection, batch_events, storage_type)

    def get_cursor(self, connection: 'psycopg2.extensions.connection'):
        cursor_name = str(uuid.uuid4())
        # Named cursors can be created only in the transaction. As our connection has autocommit set to true
        # there is not transaction concept with it so we need to have withhold to true and as this cursor is local
        # and we explicitly close it we are good
        return connection.cursor(name=cursor_name, withhold=True)

    def after_execute(self, cursor) -> None:
        super().create_result_set(cursor)


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
