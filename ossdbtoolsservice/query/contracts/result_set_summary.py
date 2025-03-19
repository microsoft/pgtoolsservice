# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List  # noqa

from ossdbtoolsservice.core.models import PGTSBaseModel
from ossdbtoolsservice.query.contracts import DbColumn
from ossdbtoolsservice.hosting import OutgoingMessageRegistration


class ResultSetSummary(PGTSBaseModel):
    id: int
    batch_id: int
    row_count: int
    complete: bool
    column_info: list[DbColumn]


OutgoingMessageRegistration.register_outgoing_message(ResultSetSummary)
