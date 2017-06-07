# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class BatchSummary(object):

    def __init__(self, 
        execution_start, 
        execution_end, 
        has_error, 
        ident, 
        selection, 
        result_set_summaries, 
        special_action):
        self.ExecutionStart = execution_start
        self.ExecutionEnd = execution_end
        self.ExecutionElapsed = self.ExecutionStart - self.ExecutionEnd
        self.HasError = has_error
        self.Id = ident
        self.Selection = selection
        self.ResultSetSummaries = result_set_summaries
        self.SpecialAction = special_action
            