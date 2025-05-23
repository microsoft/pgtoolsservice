# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
from typing import TYPE_CHECKING, Callable, Dict, List, Optional  # noqa

import sqlparse

from ossdbtoolsservice.connection import ServerConnection
from ossdbtoolsservice.query import Batch, BatchEvents, ResultSetStorageType, create_batch
from ossdbtoolsservice.query.contracts import SaveResultsRequestParams, SelectionData
from ossdbtoolsservice.query.contracts.result_set_subset import ResultSetSubset
from ossdbtoolsservice.query.data_storage import FileStreamFactory

if TYPE_CHECKING:
    from ossdbtoolsservice.query_execution.contracts.execute_request import (
        ExecutionPlanOptions,
    )


class QueryEvents:
    def __init__(
        self,
        on_query_started: Callable | None = None,
        on_query_completed: Callable | None = None,
        batch_events: BatchEvents | None = None,
    ) -> None:
        self.on_query_started = on_query_started
        self.on_query_completed = on_query_completed
        self.batch_events = batch_events


class ExecutionState(Enum):
    NOT_STARTED = ("Not Started",)
    EXECUTING = ("Executing",)
    EXECUTED = "Executed"


class QueryExecutionSettings:
    def __init__(
        self,
        execution_plan_options: "ExecutionPlanOptions",
        result_set_storage_type: ResultSetStorageType = ResultSetStorageType.FILE_STORAGE,
    ) -> None:
        self._execution_plan_options = execution_plan_options
        self._result_set_storage_type = result_set_storage_type

    @property
    def execution_plan_options(self) -> "ExecutionPlanOptions":
        return self._execution_plan_options

    @property
    def result_set_storage_type(self) -> ResultSetStorageType:
        return self._result_set_storage_type


class Query:
    """Object representing a single query, consisting of one or more batches"""

    EXPLAIN_QUERY_TEMPLATE = "EXPLAIN {0}"
    EXPLAIN_ANALYZE_QUERY_TEMPLATE = "EXPLAIN ANALYZE {0}"

    def __init__(
        self,
        owner_uri: str,
        query_text: str,
        query_execution_settings: QueryExecutionSettings,
        query_events: QueryEvents,
    ) -> None:
        self._execution_state: ExecutionState = ExecutionState.NOT_STARTED
        self._owner_uri: str = owner_uri
        self._query_text = query_text
        self._disable_auto_commit = False
        self._user_transaction = False
        self._current_batch_index = 0
        self._batches: list[Batch] = []
        self._execution_plan_options = query_execution_settings.execution_plan_options
        self._connection_backend_pid: Optional[int] = None

        self.is_canceled = False

        # Initialize the batches
        statements = sqlparse.split(query_text)
        selection_data = compute_selection_data_for_batches(statements, query_text)

        for index, batch_text in enumerate(statements):
            # Skip any empty text
            formatted_text = sqlparse.format(batch_text, strip_comments=True).strip()
            if not formatted_text or formatted_text == ";":
                continue

            sql_statement_text = batch_text

            # Create and save the batch
            if bool(self._execution_plan_options):
                # TODO: These options are unused in VSCode.
                if self._execution_plan_options.include_estimated_execution_plan_xml:
                    sql_statement_text = Query.EXPLAIN_QUERY_TEMPLATE.format(
                        sql_statement_text
                    )
                elif self._execution_plan_options.include_actual_execution_plan_xml:
                    self._disable_auto_commit = True
                    sql_statement_text = Query.EXPLAIN_ANALYZE_QUERY_TEMPLATE.format(
                        sql_statement_text
                    )

            # Check if user defined transaction
            if formatted_text.lower().startswith("begin"):
                self._disable_auto_commit = True
                self._user_transaction = True

            batch = create_batch(
                sql_statement_text,
                len(self.batches),
                selection_data[index],
                query_events.batch_events,
                query_execution_settings.result_set_storage_type,
            )

            self._batches.append(batch)

    @property
    def owner_uri(self) -> str:
        return self._owner_uri

    @property
    def execution_state(self) -> ExecutionState:
        return self._execution_state

    @property
    def query_text(self) -> str:
        return self._query_text

    @property
    def batches(self) -> list[Batch]:
        return self._batches

    @property
    def current_batch_index(self) -> int:
        return self._current_batch_index

    @property
    def connection_backend_pid(self) -> Optional[int]:
        return self._connection_backend_pid

    def execute(self, connection: ServerConnection, retry_state: bool = False) -> None:
        """
        Execute the query using the given connection

        :param connection: The connection object to use when executing the query
        :param batch_start_callback: A function to run before executing each batch
        :param batch_end_callback: A function to run after executing each batch
        :raises RuntimeError: If the query was already executed
        """
        if self._execution_state is ExecutionState.EXECUTED and not retry_state:
            raise RuntimeError("Cannot execute a query multiple times")

        self._execution_state = ExecutionState.EXECUTING

        # Set the connection backend PID
        self._connection_backend_pid = connection.backend_pid

        # Run each batch sequentially
        try:
            if connection.transaction_in_error and not self.is_rollback:
                # If the transaction is in error, the only statements we can execute
                # are ROLLBACK or ROLLBACK TO SAVEPOINT.
                raise RuntimeError(
                    "Your transaction is currently aborted due to an error. "
                    "You must explicitly issue a ROLLBACK or ROLLBACK TO SAVEPOINT "
                    "before executing further commands."
                )

            if self._user_transaction:
                connection.set_user_transaction(True)

            if self._disable_auto_commit and connection.transaction_is_idle:
                connection.autocommit = False

            for batch_index, batch in enumerate(self._batches):
                self._current_batch_index = batch_index

                if self.is_canceled:
                    break

                batch.execute(connection)

        finally:
            # If transaction is in idle (no active transaction),
            # we can set autocommit to True, if the connection is open.
            if connection.open and connection.transaction_is_idle:
                connection.autocommit = True
                connection.set_user_transaction(False)
                self._disable_auto_commit = False
            self._execution_state = ExecutionState.EXECUTED
            self._connection_backend_pid = None

    @property
    def is_rollback(self) -> bool:
        """
        Check if the query is a rollback - this is determined by checking if the first batch
        is a rollback statement.

        :return: True if the query is a rollback, False otherwise
        """
        return bool(self.batches) and self.batches[0].is_rollback

    def get_subset(
        self, batch_index: int, start_index: int, end_index: int
    ) -> ResultSetSubset:
        if batch_index < 0 or batch_index >= len(self._batches):
            raise IndexError(
                "Batch index cannot be less than 0 or greater than the number of batches"
            )

        return self._batches[batch_index].get_subset(start_index, end_index)

    def save_as(
        self,
        params: SaveResultsRequestParams,
        file_factory: FileStreamFactory,
        on_success: Callable[[], None],
        on_failure: Callable[[Exception], None],
    ) -> None:
        batch_index = params.batch_index
        if batch_index is None:
            raise ValueError("Batch index cannot be None")

        if batch_index < 0 or batch_index >= len(self.batches):
            raise IndexError(
                "Batch index cannot be less than 0 or greater than the number of batches"
            )

        self.batches[batch_index].save_as(params, file_factory, on_success, on_failure)


def compute_selection_data_for_batches(
    batches: list[str], full_text: str
) -> list[SelectionData]:
    # Map the starting index of each line to the line number
    line_map: dict[int, int] = {}
    search_offset = 0
    for line_num, line in enumerate(full_text.split("\n")):
        start_index = full_text.index(line, search_offset)
        line_map[start_index] = line_num
        search_offset = start_index + len(line)

    # Iterate through the batches to build selection data
    selection_data: list[SelectionData] = []
    search_offset = 0
    for batch in batches:
        # Calculate the starting line number and column
        start_index = full_text.index(batch, search_offset)
        start_line_index = max(
            filter(lambda line_index: line_index <= start_index, line_map.keys())
        )
        start_line_num = line_map[start_line_index]
        start_col_num = start_index - start_line_index

        # Calculate the ending line number and column
        end_index = start_index + len(batch)
        end_line_index = max(
            filter(lambda line_index: line_index < end_index, line_map.keys())
        )
        end_line_num = line_map[end_line_index]
        end_col_num = end_index - end_line_index

        # Create a SelectionData object with the results and update the search offset
        # to exclude batches that have been processed
        selection_data.append(
            SelectionData(
                start_line=start_line_num,
                start_column=start_col_num,
                end_line=end_line_num,
                end_column=end_col_num,
            )
        )
        search_offset = end_index

    return selection_data
