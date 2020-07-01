# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.query.contracts import SelectionData


class BatchSummary:

    @classmethod
    def from_batch(cls, batch):
        instance = cls(batch.id, batch.selection, batch.start_date_str, batch.has_error)

        if batch.has_executed:
            instance.execution_elapsed = batch.elapsed_time
            instance.execution_end = batch.end_time
            instance.result_set_summaries = [batch.result_set.result_set_summary] if batch.result_set is not None else []

        return instance

    def __init__(self,
                 batchId: int,
                 selection: SelectionData = None,
                 execution_start: str = None,
                 has_error: bool = False) -> None:
        self.id = batchId
        self.selection = selection
        self.execution_start: str = execution_start
        self.has_error = has_error
        self.execution_end: str = None
        self.execution_elapsed = None
        self.result_set_summaries = None
