# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from typing import List, Optional  # noqa

import psycopg2

from pgsqltoolsservice.utils.time import get_time_str, get_elapsed_time_str
from pgsqltoolsservice.query_execution.contracts.common import (  # noqa
    SelectionData, BatchSummary, ResultSetSummary
)
from pgsqltoolsservice.query_execution.result_set import ResultSet  # noqa


class Batch(object):

    def __init__(self, batch_text: str, ordinal_id: int, selection: SelectionData) -> None:
        self.batch_text = batch_text
        self.id = ordinal_id
        self.selection = selection
        self.start_time: datetime = datetime.now()
        self.has_error = False
        self.has_executed = False
        self.result_set: ResultSet = None
        self.end_time: datetime = None
        self.row_count: int = -1  # Use -1 as the default since that's what psycopg2 uses
        self.notices: List[str] = []

    def build_batch_summary(self) -> BatchSummary:
        """returns a summary of current batch status"""
        if self.start_time is None:
            self.start_time = datetime.now()
        summary = BatchSummary(self.id, self.selection, get_time_str(self.start_time), self.has_error)

        if self.has_executed:
            summary.execution_elapsed = get_elapsed_time_str(self.start_time, self.end_time)
            summary.result_set_summaries = [self.result_set.result_set_summary] if self.result_set is not None else []
            summary.execution_end = get_time_str(self.end_time)
            summary.special_action = None
        return summary

    def execute(self, cursor):
        """
        Execute the batch using the given psycopg2 cursor

        :raises psycopg2.DatabaseError: if an error is encountered while running the batch's query
        """
        try:
            cursor.execute(self.batch_text)
        except psycopg2.DatabaseError:
            self.has_error = True
            raise
        finally:
            self.has_executed = True
            self.end_time = datetime.now()
            self.notices = cursor.connection.notices
            cursor.connection.notices = []

        if cursor.description is not None:
            self.row_count = cursor.rowcount
            results = cursor.fetchall()
            self.result_set = ResultSet(0, self.id, cursor.description, cursor.rowcount, results)
