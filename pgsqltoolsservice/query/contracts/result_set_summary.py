
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List  # noqa

from pgsqltoolsservice.query.contracts import DbColumn


class ResultSetSummary:

    def __init__(self, result_set_id: int, batch_id: int, row_count: int, column_info: List[DbColumn]):
        self.id = result_set_id
        self.batch_id = batch_id
        self.row_count = row_count
        self.column_info = column_info
