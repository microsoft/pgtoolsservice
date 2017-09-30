# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
from typing import Callable, Dict, List, Optional  # noqa

import sqlparse

from pgsqltoolsservice.query import Batch, BatchEvents, create_batch, ResultSetStorageType
from pgsqltoolsservice.query.contracts import SelectionData


class QueryEvents:
    def __init__(self, on_query_started=None, on_query_completed=None, batch_events: BatchEvents= None) -> None:
        self.on_query_started = on_query_started
        self.on_query_completed = on_query_completed
        self.batch_events = batch_events


class ExecutionState(Enum):
    NOT_STARTED = 'Not Started',
    EXECUTING = 'Executing',
    EXECUTED = 'Executed'


class QueryExecutionSettings:

    def __init__(
            self, execution_plan_options,
            result_set_storage_type: ResultSetStorageType = ResultSetStorageType.IN_MEMORY
            ) -> None:

        self._execution_plan_options = execution_plan_options
        self._result_set_storage_type = result_set_storage_type

    @property
    def execution_plan_options(self):
        return self._execution_plan_options

    @property
    def result_set_storage_type(self):
        return self._result_set_storage_type


class Query:
    """Object representing a single query, consisting of one or more batches"""

    EXPLAIN_QUERY_TEMPLATE = 'EXPLAIN {0}'
    ANALYZE_EXPLAIN_QUERY_TEMPLATE = 'ANALYZE EXPLAIN {0}'

    def __init__(self, owner_uri: str, query_text: str, query_execution_settings: QueryExecutionSettings, query_events: QueryEvents) -> None:
        self._execution_state: ExecutionState = ExecutionState.NOT_STARTED
        self._owner_uri: str = owner_uri
        self._query_text = query_text

        self._disable_auto_commit = False
        self._current_batch_index = 0
        self._is_canceled = False
        self._batches: List[Batch] = []
        self._execution_plan_options = query_execution_settings.execution_plan_options

        # Initialize the batches
        statements = sqlparse.split(query_text)
        selection_data = compute_selection_data_for_batches(statements, query_text)

        for index, batch_text in enumerate(statements):
            # Skip any empty text
            formatted_text = sqlparse.format(batch_text, strip_comments=True).strip()
            if not formatted_text or formatted_text == ';':
                continue
            # Create and save the batch
            if bool(self._execution_plan_options):
                if self._execution_plan_options.include_estimated_execution_plan_xml:
                    formatted_text = Query.EXPLAIN_QUERY_TEMPLATE.format(formatted_text)
                elif self._execution_plan_options.include_actual_execution_plan_xml:
                    self._disable_auto_commit = True
                    formatted_text = Query.ANALYZE_EXPLAIN_QUERY_TEMPLATE.format(formatted_text)

            batch = create_batch(
                formatted_text,
                len(self.batches),
                selection_data[index],
                query_events.batch_events,
                query_execution_settings.result_set_storage_type)

            self._batches.append(batch)

    @property
    def owner_uri(self) -> str:
        return self._owner_uri

    @property
    def is_canceled(self) -> bool:
        return self._is_canceled

    @is_canceled.setter
    def is_canceled(self, is_canceled) -> None:
        self._is_canceled = is_canceled

    @property
    def execution_state(self) -> ExecutionState:
        return self._execution_state

    @property
    def query_text(self) -> str:
        return self._query_text

    @property
    def batches(self) -> List[Batch]:
        return self._batches

    @property
    def current_batch_index(self) -> int:
        return self._current_batch_index

    def execute(self, connection: 'psycopg2.extensions.connection'):
        """
        Execute the query using the given connection

        :param connection: The psycopg2 connection to use when executing the query
        :param batch_start_callback: A function to run before executing each batch
        :param batch_end_callback: A function to run after executing each batch
        :raises RuntimeError: If the query was already executed
        :raises QueryExecutionError: If there was an error while running the query
        """
        if self._execution_state is ExecutionState.EXECUTED:
            raise RuntimeError('Cannot execute a query multiple times')

        self._execution_state = ExecutionState.EXECUTING

        # Run each batch sequentially
        try:
            current_auto_commit_status = connection.autocommit
            # When Analyze Explain is used we have to disable auto commit
            if self._disable_auto_commit:
                connection.autocommit = False

            for batch_index, batch in enumerate(self._batches):
                self._current_batch_index = batch_index

                if self.is_canceled:
                    break

                batch.execute(connection)
        finally:
            connection.autocommit = current_auto_commit_status
            self._execution_state = ExecutionState.EXECUTED


def compute_selection_data_for_batches(batches: List[str], full_text: str) -> List[SelectionData]:
    # Map the starting index of each line to the line number
    line_map: Dict[int, int] = {}
    search_offset = 0
    for line_num, line in enumerate(full_text.split('\n')):
        start_index = full_text.index(line, search_offset)
        line_map[start_index] = line_num
        search_offset = start_index + len(line)

    # Iterate through the batches to build selection data
    selection_data: List[SelectionData] = []
    search_offset = 0
    for batch in batches:
        # Calculate the starting line number and column
        start_index = full_text.index(batch, search_offset)
        start_line_index = max(filter(lambda line_index: line_index <= start_index, line_map.keys()))
        start_line_num = line_map[start_line_index]
        start_col_num = start_index - start_line_index

        # Calculate the ending line number and column
        end_index = start_index + len(batch)
        end_line_index = max(filter(lambda line_index: line_index < end_index, line_map.keys()))
        end_line_num = line_map[end_line_index]
        end_col_num = end_index - end_line_index

        # Create a SelectionData object with the results and update the search offset to exclude batches that have been processed
        selection_data.append(SelectionData(start_line_num, start_col_num, end_line_num, end_col_num))
        search_offset = end_index

    return selection_data
