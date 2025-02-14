# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import List  # noqa

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.edit_data.contracts import SessionOperationRequest


class CreateRowRequest(SessionOperationRequest):
    def __init__(self):
        SessionOperationRequest.__init__(self)


class CreateRowResponse:
    def __init__(self, new_row_id: int, default_values: List[str]):
        self.default_values = default_values
        self.new_row_id = new_row_id


CREATE_ROW_REQUEST = IncomingMessageConfiguration("edit/createRow", CreateRowRequest)
