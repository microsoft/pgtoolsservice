# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.serialization import Serializable


class SessionOperationRequest(Serializable):
    owner_uri: str

    def __init__(self):
        self.owner_uri = None


class RowOperationRequest(SessionOperationRequest):
    row_id: int

    def __init__(self):
        SessionOperationRequest.__init__(self)
        self.row_id = None
