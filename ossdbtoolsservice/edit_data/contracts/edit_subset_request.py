# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import List

from ossdbtoolsservice.edit_data.contracts import EditRow
from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)
from ossdbtoolsservice.serialization import Serializable


class EditSubsetParams(Serializable):
    owner_uri: str
    row_start_index: int
    row_count: int

    def __init__(self):
        self.owner_uri: str = None
        self.row_start_index: int = None
        self.row_count: int = None


class EditSubsetResponse:
    def __init__(self, row_count: int, edit_rows: List[EditRow]):
        self.row_count = row_count
        self.subset = edit_rows


EDIT_SUBSET_REQUEST = IncomingMessageConfiguration("edit/subset", EditSubsetParams)
OutgoingMessageRegistration.register_outgoing_message(EditSubsetResponse)
