# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from datetime import datetime
from pgsqltoolsservice.query_execution.result_set import ResultSet
from pgsqltoolsservice.query_execution.selection_data import SelectionData
from pgsqltoolsservice.query_execution.batch_summary import BatchSummary

#TODO: Convert any dates to properly formatted strings

class Batch(object):

    def __init__(self, ordinalId: int, selection: SelectionData, has_error: bool):
        self.id = ordinalId
        self.selection = selection
        self.start_time = datetime.now()
        self.has_error = has_error
        self.has_executed = False #TODO: Find in sqltoolsservice where hasExecuted changes value
        self.result_sets = []
        self.end_time: datetime = None

    def build_batch_summary(self) -> BatchSummary:
        """returns a summary of current batch status"""
        start_time_str = get_time_str(self.start_time)
        summary = BatchSummary(self.id, self.selection, start_time_str, self.has_error)

        if self.has_executed:
            #TODO handle multiple result set summaries later
            elapsed_time = get_elapsed_time_str(self.start_time, self.end_time)
            summary.resultSetSummaries = self.get_result_set_summaries()
            summary.executionEnd = self.end_time
            summary.executionElapsed = elapsed_time
            summary.SpecialAction = None
        return summary

    #TODO: Assuming one result set for now. Handle for multiple later
    def get_result_set_summaries(self):
        """Gets result sets as summary contract objects"""
        if not self.result_sets:
            # No resultsets were set
            return None
        return self.result_sets[0].generate_result_set_summary()

def get_time_str(time: datetime):
    """Convert a time object into a standard user-readable string"""
    return time.strftime('%H:%M:%S.%f')

def get_elapsed_time_str(start_time: datetime, end_time: datetime):
    """Get time difference between two times as a user-readable string"""
    elapsed_time = end_time - start_time
    return get_time_str(elapsed_time)


