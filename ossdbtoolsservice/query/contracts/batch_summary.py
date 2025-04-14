# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import TYPE_CHECKING

from ossdbtoolsservice.core.models import PGTSBaseModel
from ossdbtoolsservice.hosting import OutgoingMessageRegistration
from ossdbtoolsservice.query.contracts import SelectionData
from ossdbtoolsservice.query.contracts.result_set_summary import ResultSetSummary

if TYPE_CHECKING:
    from ossdbtoolsservice.query.batch import Batch


class BatchSummary(PGTSBaseModel):
    id: int
    selection: SelectionData | None = None
    execution_start: str | None = None
    has_error: bool = False
    execution_end: str | None = None
    execution_elapsed: str | None = None
    result_set_summaries: list[ResultSetSummary] | None = None

    @classmethod
    def from_batch(cls, batch: "Batch") -> "BatchSummary":
        return cls(
            id=batch.id,
            selection=batch.selection,
            execution_start=batch.start_date_str,
            has_error=batch.has_error,
            execution_end=batch.end_time if batch.has_executed else None,
            execution_elapsed=batch.elapsed_time if batch.has_executed else None,
            result_set_summaries=(
                [batch.result_set.result_set_summary] if batch.result_set is not None else []
            )
            if batch.has_executed
            else None,
        )


OutgoingMessageRegistration.register_outgoing_message(BatchSummary)
