# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import List # noqa

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.edit_data.contracts import SessionOperationRequest


class CreateRowRequest(SessionOperationRequest):

    def __init__(self):
        SessionOperationRequest.__init__(self)


class CreateRowResponse:

    def __init__(self):
        self.default_values: List[str] = []
        self.new_row_id = None


CREATE_ROW_REQUEST = IncomingMessageConfiguration('edit/createRow', CreateRowRequest)
