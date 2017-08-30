# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from enum import Enum
from typing import Callable, Dict, List, Optional  # noqa

import sqlparse

from pgsqltoolsservice.query_execution.batch import Batch
from pgsqltoolsservice.query_execution.contracts import SelectionData


class ExecutionState(Enum):
    NOT_STARTED = 'Not Started',
    EXECUTING = 'Executing',
    EXECUTED = 'Executed'


class Query:
    """Object representing a single query, consisting of one or more batches"""

    def __init__(self, owner_uri: str, query_text: str) -> None:
        self.execution_state: ExecutionState = ExecutionState.NOT_STARTED
        self.is_canceled = False
        self.owner_uri: str = owner_uri
        self.batches: List[Batch] = []
        self.query_text = query_text
        self.current_batch_index = 0

        # Initialize the batches
        statements = sqlparse.split(query_text)
        selection_data = _compute_selection_data_for_batches(statements, query_text)
        for index, batch_text in enumerate(statements):
            # Skip any empty text
            formatted_text = sqlparse.format(batch_text, strip_comments=True).strip()
            if not formatted_text or formatted_text == ';':
                continue
            # Create and save the batch
            batch = Batch(formatted_text, len(self.batches), selection_data[index])
            self.batches.append(batch)

    def execute(self, connection, batch_start_callback: Callable[['Query', Batch], None] = None, batch_end_callback: Callable[['Query', Batch], None] = None):
        """
        Execute the query using the given connection

        :param connection: The psycopg2 connection to use when executing the query
        :param batch_start_callback: A function to run before executing each batch
        :param batch_end_callback: A function to run after executing each batch
        :raises RuntimeError: If the query was already executed
        :raises QueryExecutionError: If there was an error while running the query
        """
        if self.execution_state is ExecutionState.EXECUTED:
            raise RuntimeError('Cannot execute a query multiple times')

        # Run each batch sequentially
        try:
            for batch_index, batch in enumerate(self.batches):
                self.current_batch_index = batch_index
                if self.is_canceled:
                    break
                if batch_start_callback is not None:
                    batch_start_callback(self, batch)
                try:
                    cursor = connection.cursor()
                    batch.execute(cursor)
                finally:
                    cursor.close()
                    if batch_end_callback is not None:
                        batch_end_callback(self, batch)
        finally:
            self.execution_state = ExecutionState.EXECUTED


def _compute_selection_data_for_batches(batches: List[str], full_text: str) -> List[SelectionData]:
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
        end_col_num = end_index - end_line_index - 1

        # Create a SelectionData object with the results and update the search offset to exclude batches that have been processed
        selection_data.append(SelectionData(start_line_num, start_col_num, end_line_num, end_col_num))
        search_offset = end_index
    return selection_data
