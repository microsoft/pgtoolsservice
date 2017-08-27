# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import List # noqa

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.edit_data.contracts import SessionOperationRequest
import pgsqltoolsservice.utils as utils


class CreateRowRequest(SessionOperationRequest):
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self):
        pass


class CreateRowResponse:

    def __init__(self):
        self.default_values: List[str] = []
        self.new_row_id = None


CREATE_ROW_REQUEST = IncomingMessageConfiguration('edit/createRow', CreateRowRequest)
