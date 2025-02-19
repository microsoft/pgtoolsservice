# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.edit_data.contracts import EditRow
from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)
from ossdbtoolsservice.serialization import Serializable


class EditSubsetParams(Serializable):
    owner_uri: str | None
    row_start_index: int | None
    row_count: int | None

    def __init__(self) -> None:
        self.owner_uri = None
        self.row_start_index = None
        self.row_count = None


class EditSubsetResponse:
    def __init__(self, row_count: int, edit_rows: list[EditRow]) -> None:
        self.row_count = row_count
        self.subset = edit_rows


EDIT_SUBSET_REQUEST = IncomingMessageConfiguration("edit/subset", EditSubsetParams)
OutgoingMessageRegistration.register_outgoing_message(EditSubsetResponse)
