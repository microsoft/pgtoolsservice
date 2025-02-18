# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List  # noqa

from ossdbtoolsservice.query.contracts import DbColumn
from ossdbtoolsservice.hosting import OutgoingMessageRegistration


class ResultSetSummary:
    id: int
    batch_id: int
    row_count: int
    complete: bool
    column_info: list[DbColumn]

    def __init__(
        self,
        result_set_id: int,
        batch_id: int,
        row_count: int,
        complete: bool,
        column_info: list[DbColumn],
    ):
        self.id = result_set_id
        self.batch_id = batch_id
        self.row_count = row_count
        self.complete = complete
        self.column_info = column_info


OutgoingMessageRegistration.register_outgoing_message(ResultSetSummary)
