# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from datetime import datetime
from dateutil import parser
from pgsqltoolsservice.query_execution.contracts.common import (SelectionData, BatchSummary)


# TODO: Convert any dates to properly formatted strings

class Batch(object):

    def __init__(self, ordinal_id: int, selection: SelectionData, has_error: bool):
        self.id = ordinal_id
        self.selection = selection
        self.start_time: str = get_time_str(datetime.now())
        self.has_error = has_error
        self.has_executed = False  # TODO: Find in sqltoolsservice where hasExecuted changes value
        self.result_sets = []
        self.end_time: str = None

    def build_batch_summary(self) -> BatchSummary:
        """returns a summary of current batch status"""
        summary = BatchSummary(self.id, self.selection, self.start_time, self.has_error)

        if self.has_executed:
            # TODO handle multiple result set summaries later
            elapsed_time = get_elapsed_time_str(self.start_time, self.end_time)
            summary.result_set_summaries = self.get_result_set_summaries()
            summary.execution_end = self.end_time
            summary.execution_elapsed = elapsed_time
            summary.special_action = None
        return summary

    # TODO: Assuming one result set for now. Handle for multiple later (list needed for query complete response)
    def get_result_set_summaries(self):
        """Gets result sets as summary contract objects"""
        if not self.result_sets:
            # No resultsets were set
            return None
        return self.result_sets[0].generate_result_set_summary()


def get_time_str(time: datetime):
    """Convert a time object into a standard user-readable string"""
    return time.strftime('%H:%M:%S.%f')


def get_elapsed_time_str(start_time: str, end_time: str):
    """Get time difference between two times as a user-readable string"""
    elapsed_time = parser.parse(end_time) - parser.parse(start_time)
    return str(elapsed_time)
