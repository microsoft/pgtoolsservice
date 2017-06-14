# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from typing import List

from pgsqltoolsservice.utils.time import get_time_str, get_elapsed_time_str
from pgsqltoolsservice.query_execution.contracts.common import (
    SelectionData, BatchSummary, ResultSetSummary, ResultSetSubset
)


class Batch(object):

    def __init__(self, ordinal_id: int, selection: SelectionData, has_error: bool):
        self.id = ordinal_id
        self.selection = selection
        self.start_time: datetime = datetime.now()
        self.has_error = has_error
        self.has_executed = False
        self.result_sets = []
        self.end_time: datetime = None

    def build_batch_summary(self) -> BatchSummary:
        """returns a summary of current batch status"""
        summary = BatchSummary(self.id, self.selection, self.start_time, self.has_error)

        if self.has_executed:
            # TODO handle multiple result set summaries later
            elapsed_time = get_elapsed_time_str(self.start_time, self.end_time)
            summary.execution_elapsed = elapsed_time
            summary.result_set_summaries: List[ResultSetSummary] = self.get_result_set_summaries()
            summary.execution_end = get_time_str(self.end_time)
            summary.special_action = None
        return summary

    def get_result_set_summaries(self) -> List[ResultSetSummary]:
        """Gets result sets as summary contract objects"""
        if not self.result_sets:
            # No resultsets were set
            return None
        result_set_summaries = []
        for result_set in self.result_sets:
            result_set_summaries.append(result_set.generate_result_set_summary())
        return result_set_summaries
    
    def get_subset(self, result_set_index, start_row, row_count) -> ResultSetSubset:
        """
            Gets a subset of the result sets indicated by the
            index, start row, and row count
        """
        self.result_sets[result_set_index]
        



