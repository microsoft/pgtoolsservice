# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class BatchSummary(object):

    def __init__(self, ident, selection, execution_start, has_error, result_set_summaries, special_action):
        self.Id = ident
        self.Selection = selection
        self.ExecutionStart = execution_start
        self.HasError = has_error
        self.ResultSetSummaries = result_set_summaries
        self.SpecialAction = special_action
        