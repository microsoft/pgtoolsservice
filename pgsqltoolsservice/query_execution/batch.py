# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from datetime import date

class Batch(object):

    def __init__(self, ident, selection, execution_start_time, has_error):
        self.Id = ident
        self.Selection = selection
        self.executionStartTime = execution_start_time
        self.HasError = has_error
        self.HasExecuted = False #TODO: Find in sqltoolsservice where hasExecuted changes value
        self.ResultsSets = []

    def build_batch_summary(self):
        summary.Id = self.Id
        summary.Selection = self.Selection
        summary.ExecutionStart = execution_start_time_stamp()
        summary.HasError = self.HasError

        if self.HasExecuted:
            summary.ResultSetSummaries = ResultSummaries()
            summary.ExecutionEnd = ExecutionEndTimeStamp()
            summary.ExecutionElapsed = ExecutionElapsedTime()
            summary.SpecialAction = process_results_set_special_actions()
        return summary
    
    def process_results_set_special_actions(self):
        #assuming we're only going to ever have one batch, therefore only one result set
        return self.ResultsSets[0].Summary.SpecialAction

    #TODO: Properly format the time
    def execution_start_time_stamp(self):
        return str(self.executionStartTime)
    
    #TODO: Properly format the time
    def execution_end_time_stamp(self):
        return str(self.executionEndTime)







