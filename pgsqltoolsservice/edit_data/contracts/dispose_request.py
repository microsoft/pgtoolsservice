# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.edit_data.contracts import SessionOperationRequest
import pgsqltoolsservice.utils as utils


class DisposeRequest(SessionOperationRequest):
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self):
        pass


class DisposeResponse:

    def __init__(self):
        pass


DISPOSE_REQUEST = IncomingMessageConfiguration('edit/dispose', DisposeRequest)
