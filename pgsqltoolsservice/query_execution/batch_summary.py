# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.query_execution.selection_data import SelectionData

class BatchSummary(object):

    def __init__(self,
                 batchId: int,
                 selection: SelectionData = None,
                 execution_start: str = None,
                 has_error: bool = False):
        self.id = batchId
        self.selection = selection
        self.executionStart: str = execution_start
        self.hasError = has_error
        self.executionEnd: str = None
        self.executionElapsed = None
        self.resultSetSummaries = None
        self.specialAction = None
            