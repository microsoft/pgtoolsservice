# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.edit_data.contracts import SessionOperationRequest
import pgsqltoolsservice.utils as utils


class DeleteRowRequest(SessionOperationRequest):
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self):
        pass


class DeleteRowResponse:

    def __init__(self):
        pass


DELETE_ROW_REQUEST = IncomingMessageConfiguration('edit/deleteRow', DeleteRowRequest)
