# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional  # noqa

import sqlparse
from ossdbtoolsservice.driver import ServerConnection
from ossdbtoolsservice.query import Batch, BatchEvents, create_batch, ResultSetStorageType
from ossdbtoolsservice.query.contracts import SaveResultsRequestParams, SelectionData
from ossdbtoolsservice.query.data_storage import FileStreamFactory
import psycopg


class QueryEvents:
    def __init__(self, on_query_started=None, on_query_completed=None, batch_events: BatchEvents = None) -> None:
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
            result_set_storage_type: ResultSetStorageType = ResultSetStorageType.FILE_STORAGE
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
        self._user_transaction = False
        self._current_batch_index = 0
        self._batches: List[Batch] = []
        self._execution_plan_options = query_execution_settings.execution_plan_options
        self._query_events = query_events
        self._query_execution_settings = query_execution_settings

        self.is_canceled = False

        # Initialize the batches
        # statements = sqlparse.split(query_text)
        # selection_data = compute_selection_data_for_batches([query_text], query_text)

        # # for index, batch_text in enumerate(statements):
        # index = 0
        # batch_text = query_text
        # # Skip any empty text
        # # formatted_text = sqlparse.format(batch_text, strip_comments=True).strip()
        # # if not formatted_text or formatted_text == ';':
        # #     return None
        # formatted_text = batch_text

        # sql_statement_text = batch_text

        # # Create and save the batch
        # if bool(self._execution_plan_options):
        #     if self._execution_plan_options.include_estimated_execution_plan_xml:
        #         sql_statement_text = Query.EXPLAIN_QUERY_TEMPLATE.format(sql_statement_text)
        #     elif self._execution_plan_options.include_actual_execution_plan_xml:
        #         self._disable_auto_commit = True
        #         sql_statement_text = Query.ANALYZE_EXPLAIN_QUERY_TEMPLATE.format(sql_statement_text)

        # # Check if user defined transaction
        # if formatted_text.lower().startswith('begin'):
        #     self._disable_auto_commit = True
        #     self._user_transaction = True

        # batch = create_batch(
        #     sql_statement_text,
        #     len(self.batches),
        #     selection_data[index],
        #     query_events.batch_events,
        #     query_execution_settings.result_set_storage_type)

        # self._batches.append(batch)

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
    def batches(self) -> List[Batch]:
        return self._batches

    @property
    def current_batch_index(self) -> int:
        return self._current_batch_index
    
    @property
    def query_events(self) -> QueryEvents:
        return self._query_events
    
    @property
    def query_execution_settings(self) -> QueryExecutionSettings:
        return self._query_execution_settings

    def execute(self, connection: ServerConnection, retry_state=False):
        """
        Execute the query using the given connection

        :param connection: The connection object to use when executing the query
        :param batch_start_callback: A function to run before executing each batch
        :param batch_end_callback: A function to run after executing each batch
        :raises RuntimeError: If the query was already executed
        """
        if self._execution_state is ExecutionState.EXECUTED and not retry_state:
            raise RuntimeError('Cannot execute a query multiple times')

        self._execution_state = ExecutionState.EXECUTING

        # Run each batch sequentially
        try:
            if self._user_transaction:
                connection.set_user_transaction(True)

            # When Analyze Explain is used we have to disable auto commit
            if self._disable_auto_commit and connection.transaction_is_idle:
                connection.autocommit = False

            # for batch_index, batch in enumerate(self._batches):
            #     self._current_batch_index = batch_index

            #     if self.is_canceled:
            #         break

            # Start a cursor block
            batch_events: BatchEvents = None
            if self.query_events is not None and self.query_events.batch_events is not None:
                batch_events = self.query_events.batch_events
            with connection.cursor() as cur:
                connection.connection.add_notice_handler(lambda msg: self.notice_handler(msg, connection))
                batch_ordinal = 0
                cur.execute(self.query_text)
                curr_resultset = True
                while curr_resultset:
                    batch_obj = create_batch(
                        None,
                        batch_ordinal,
                        None,
                        self.query_events.batch_events,
                        self.query_execution_settings.result_set_storage_type,
                        # Cursor description will have a result if it contains tuples
                        True
                    )

                    # use callbacks
                    if batch_events and batch_events._on_execution_started:
                        batch_events._on_execution_started(batch_obj)

                    batch_obj.after_execute(cur)

                    if batch_events and batch_events._on_execution_completed:
                        batch_events._on_execution_completed(batch_obj)

                    if cur and cur.statusmessage is not None:
                        batch_obj.status_message = cur.statusmessage

                    batch_obj._has_executed = True

                    # Append the batch object and update while loop values
                    self.batches.append(batch_obj)
                    curr_resultset = cur.nextset()
                    batch_ordinal += 1


        finally:
            # We can only set autocommit when the connection is open.
            if connection.open and connection.transaction_is_idle:
                connection.autocommit = True
                connection.set_user_transaction(False)
                self._disable_auto_commit = False
            self._execution_state = ExecutionState.EXECUTED
    
    def notice_handler(self, notice: str, conn: ServerConnection):
        if not conn.user_transaction:
            self._notices.append('{0}: {1}'.format(notice.severity, notice.message_primary))
        elif not notice.message_primary == 'there is already a transaction in progress':
            self._notices.append('WARNING: {0}'.format(notice.message_primary))

    def get_subset(self, batch_index: int, start_index: int, end_index: int):
        if batch_index < 0 or batch_index >= len(self._batches):
            raise IndexError('Batch index cannot be less than 0 or greater than the number of batches')

        return self._batches[batch_index].get_subset(start_index, end_index)

    def save_as(self, params: SaveResultsRequestParams, file_factory: FileStreamFactory, on_success, on_failure):
        if params.batch_index < 0 or params.batch_index >= len(self.batches):
            raise IndexError('Batch index cannot be less than 0 or greater than the number of batches')

        self.batches[params.batch_index].save_as(params, file_factory, on_success, on_failure)


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
    line_map_keys = sorted(line_map.keys())
    l, r = 0, 0
    start_line_index, end_line_index = 0, 0
    for batch in batches:
        # Calculate the starting line number and column
        start_index = full_text.index(batch, search_offset) # batch start index
        # start_line_index = max(filter(lambda line_index: line_index <= start_index, line_map_keys)) # find the character index of the batch start line
        while l < len(line_map_keys) and line_map_keys[l] <= start_index:
            start_line_index = line_map_keys[l]
            l += 1

        start_line_num = line_map[start_line_index] # map that to the line number
        start_col_num = start_index - start_line_index 

        # Calculate the ending line number and column
        end_index = start_index + len(batch)
        # end_line_index = max(filter(lambda line_index: line_index < end_index, line_map_keys))
        while r < len(line_map_keys) and line_map_keys[r] < end_index:
            end_line_index = line_map_keys[r]
            r += 1
        end_line_num = line_map[end_line_index]
        end_col_num = end_index - end_line_index

        # Create a SelectionData object with the results and update the search offset to exclude batches that have been processed
        selection_data.append(SelectionData(start_line_num, start_col_num, end_line_num, end_col_num))
        search_offset = end_index

    return selection_data
