# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from enum import Enum
from typing import Callable, List, Optional  # noqa

import sqlparse

from pgsqltoolsservice.hosting import RequestContext
from pgsqltoolsservice.query_execution.batch import Batch


class ExecutionState(Enum):
    NOT_STARTED = 'Not Started',
    EXECUTING = 'Executing',
    EXECUTED = 'Executed'


class Query:
    """Object representing a single query, consisting of one or more batches"""

    def __init__(self, owner_uri: str, query_text: str, request_context: RequestContext = None):
        self.execution_state: ExecutionState = ExecutionState.NOT_STARTED
        self.is_canceled = False
        self.owner_uri: str = owner_uri
        self.batches: List[Batch] = []
        self.request_context: Optional[RequestContext] = request_context
        self.query_text = query_text
        self.current_batch_index = 0

        # Initialize the batches
        for batch_text in sqlparse.split(query_text):
            # Skip any empty text
            if not batch_text.strip():
                continue
            # Create and save the batch
            batch = Batch(batch_text, len(self.batches), None, request_context)  # TODO: Save the selection of the batch
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
