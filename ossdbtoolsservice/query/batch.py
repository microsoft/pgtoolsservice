# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import uuid
from datetime import datetime
from enum import Enum
from typing import Callable

import psycopg
import sqlparse
from psycopg import sql
from psycopg.errors import Diagnostic

from ossdbtoolsservice.connection import ServerConnection
from ossdbtoolsservice.query.contracts import (
    BatchSummary,
    SaveResultsRequestParams,
    SelectionData,
)
from ossdbtoolsservice.query.contracts.result_set_subset import ResultSetSubset
from ossdbtoolsservice.query.data_storage import FileStreamFactory
from ossdbtoolsservice.query.file_storage_result_set import FileStorageResultSet
from ossdbtoolsservice.query.in_memory_result_set import InMemoryResultSet
from ossdbtoolsservice.query.result_set import ResultSet
from ossdbtoolsservice.utils.time import get_elapsed_time_str, get_time_str


class ResultSetStorageType(Enum):
    IN_MEMORY = (1,)
    FILE_STORAGE = 2


class BatchEvents:
    def __init__(
        self,
        on_execution_started: Callable[["Batch"], None] | None = None,
        on_execution_completed: Callable[["Batch"], None] | None = None,
        on_result_set_completed: Callable[["Batch"], None] | None = None,
    ) -> None:
        self._on_execution_started = on_execution_started
        self._on_execution_completed = on_execution_completed
        self._on_result_set_completed = on_result_set_completed


class SelectBatchEvents(BatchEvents):
    def __init__(
        self,
        on_execution_started: Callable[["Batch"], None] | None,
        on_execution_completed: Callable[["Batch"], None] | None,
        on_result_set_completed: Callable[["Batch"], None] | None,
        on_after_first_fetch: Callable[["Batch"], None] | None,
    ) -> None:
        BatchEvents.__init__(
            self, on_execution_started, on_execution_completed, on_result_set_completed
        )
        self._on_after_first_fetch = on_after_first_fetch

    @classmethod
    def from_events(
        cls,
        events: BatchEvents,
        on_after_first_fetch: Callable[["Batch"], None] | None = None,
    ) -> "SelectBatchEvents":
        if isinstance(events, SelectBatchEvents):
            return events
        return cls(
            events._on_execution_started,
            events._on_execution_completed,
            events._on_result_set_completed,
            on_after_first_fetch,
        )


class Batch:
    def __init__(
        self,
        batch_text: str,
        ordinal: int,
        selection: SelectionData,
        batch_events: BatchEvents | None = None,
        storage_type: ResultSetStorageType = ResultSetStorageType.FILE_STORAGE,
    ) -> None:
        self.id = ordinal
        self.selection = selection
        self.batch_text = batch_text
        self.status_message: str | None = None

        self._execution_start_time: datetime | None = None
        self._has_error = False
        self._has_executed = False
        self._execution_end_time: datetime | None = None
        self._result_set: ResultSet | None = None
        self._notices: list[str] = []
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
    def start_date_str(self) -> str | None:
        if self._execution_start_time is None:
            return None
        return self._execution_start_time.isoformat()

    @property
    def start_time(self) -> str | None:
        return (
            get_time_str(self._execution_start_time) if self._execution_start_time else None
        )

    @property
    def end_time(self) -> str | None:
        return get_time_str(self._execution_end_time) if self._execution_end_time else None

    @property
    def elapsed_time(self) -> str | None:
        if self._execution_start_time is None or self._execution_end_time is None:
            return None
        return get_elapsed_time_str(self._execution_start_time, self._execution_end_time)

    @property
    def result_set(self) -> ResultSet | None:
        return self._result_set

    @property
    def row_count(self) -> int:
        return self.result_set.row_count if self.result_set is not None else -1

    @property
    def notices(self) -> list[str]:
        return self._notices

    @property
    def is_rollback(self) -> bool:
        return self.batch_text.lower().startswith("rollback")

    def get_cursor(self, connection: ServerConnection) -> psycopg.Cursor:
        return connection.cursor()

    def execute(self, conn: ServerConnection) -> None:
        """
        Execute the batch using a cursor retrieved from the given connection

        :raises DatabaseError: if an error is encountered while running the batch's query
        """
        self._execution_start_time = datetime.now()

        cursor: psycopg.Cursor | None = None

        if self._batch_events and self._batch_events._on_execution_started:
            self._batch_events._on_execution_started(self)
        try:
            cursor = self.get_cursor(conn)

            conn.connection.add_notice_handler(lambda msg: self.notice_handler(msg, conn))

            if self.batch_text.startswith("begin") and conn.transaction_in_trans:
                self._notices.append("WARNING: there is already a transaction in progress")

            batch_sql = sql.SQL(self.batch_text)  #  type: ignore
            cursor.execute(batch_sql)

            # Commit the transaction if autocommit is True
            if conn.autocommit:
                conn.commit()

            self.after_execute(cursor)
        except:
            self._has_error = True
            raise
        finally:
            if cursor and cursor.statusmessage is not None:
                self.status_message = cursor.statusmessage
            # We are doing this because when the execute fails for named cursors
            # cursor is not activated on the server which results in failure on close
            # Hence we are checking if the cursor was really executed for us to close it
            if cursor and cursor.rowcount != -1 and cursor.rowcount is not None:
                cursor.close()
            self._has_executed = True
            self._execution_end_time = datetime.now()

            if self._batch_events and self._batch_events._on_execution_completed:
                self._batch_events._on_execution_completed(self)

    def after_execute(self, cursor: psycopg.Cursor) -> None:
        if cursor.description is not None:
            self.create_result_set(cursor)

    def create_result_set(self, cursor: psycopg.Cursor) -> None:
        result_set = create_result_set(self._storage_type, 0, self.id)
        result_set.read_result_to_end(cursor)
        self._result_set = result_set

    def get_subset(self, start_index: int, end_index: int) -> ResultSetSubset:
        if self._result_set is None:
            raise ValueError("No result set.")
        return self._result_set.get_subset(start_index, end_index)

    def save_as(
        self,
        params: SaveResultsRequestParams,
        file_factory: FileStreamFactory,
        on_success: Callable[[], None],
        on_failure: Callable[[Exception], None],
    ) -> None:
        if params.result_set_index != 0:
            raise IndexError("Result set index should be always 0")

        if self._result_set is None:
            raise ValueError("No result set.")

        self._result_set.save_as(params, file_factory, on_success, on_failure)

    def notice_handler(self, notice: Diagnostic, conn: ServerConnection) -> None:
        if not conn.user_transaction:
            self._notices.append(f"{notice.severity}: {notice.message_primary}")
        elif notice.message_primary != "there is already a transaction in progress":
            self._notices.append(f"WARNING: {notice.message_primary}")


class SelectBatch(Batch):
    def __init__(
        self,
        batch_text: str,
        ordinal: int,
        selection: SelectionData,
        batch_events: SelectBatchEvents | None,
        storage_type: ResultSetStorageType,
    ) -> None:
        Batch.__init__(self, batch_text, ordinal, selection, batch_events, storage_type)

    def get_cursor(self, connection: ServerConnection) -> psycopg.Cursor:
        cursor_name = str(uuid.uuid4())
        # Named cursors can be created only in the transaction.
        # As our connection has autocommit set to true
        # there is not transaction concept with it so we need to have withhold to true
        # and as this cursor is local
        # and we explicitly close it we are good
        return connection.cursor(name=cursor_name, withhold=True)

    def after_execute(self, cursor: psycopg.Cursor) -> None:
        super().create_result_set(cursor)


def create_result_set(
    storage_type: ResultSetStorageType, result_set_id: int, batch_id: int
) -> ResultSet:
    if storage_type is ResultSetStorageType.FILE_STORAGE:
        return FileStorageResultSet(result_set_id, batch_id)

    return InMemoryResultSet(result_set_id, batch_id)


def create_batch(
    batch_text: str,
    ordinal: int,
    selection: SelectionData,
    batch_events: BatchEvents | None,
    storage_type: ResultSetStorageType,
) -> Batch:
    sql = sqlparse.parse(batch_text)
    statement = sql[0]

    if statement.get_type().lower() == "select":
        into_checker = [True for token in statement.tokens if token.normalized == "INTO"]
        cte_checker = [
            True for token in statement.tokens if token.ttype == sqlparse.tokens.Keyword.CTE
        ]
        if (
            len(into_checker) == 0 and len(cte_checker) == 0
        ):  # SELECT INTO and CTE keywords can't be used in named cursor
            return SelectBatch(
                batch_text,
                ordinal,
                selection,
                SelectBatchEvents.from_events(batch_events) if batch_events else None,
                storage_type,
            )

    return Batch(batch_text, ordinal, selection, batch_events, storage_type)
