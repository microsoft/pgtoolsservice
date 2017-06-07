# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from datetime import datetime
from pgsqltoolsservice.query_execution.result_set import ResultSet

#TODO: Convert any dates to properly formatted strings

class Batch(object):

    def __init__(self, ident, selection, has_error):
        self.Id = ident
        self.Selection = selection
        self.executionStartTime = datetime.datetime.now()
        self.HasError = has_error
        self.HasExecuted = False #TODO: Find in sqltoolsservice where hasExecuted changes value
        self.ResultsSets = []

    def build_batch_summary(self):
        summary = None
        summary.Id = self.Id
        summary.Selection = self.Selection
        summary.ExecutionStart = self.executionStartTime
        summary.HasError = self.HasError

        if self.HasExecuted:
            #TODO handle multiple result set summaries later
            summary.ResultSetSummaries = self.get_result_set_summaries()
            summary.ExecutionEnd = datetime.datetime.now()
            summary.ExecutionElapsed = summary.ExecutionEnd - self.executionStartTime
            summary.SpecialAction = None
        return summary

    #TODO: Assuming one result set for now. Handle for multiple later
    def get_result_set_summaries(self):
        return self.ResultsSets[0].generate_result_set_summary()







