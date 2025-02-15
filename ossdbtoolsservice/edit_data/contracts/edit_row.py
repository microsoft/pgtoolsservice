# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from enum import Enum

from ossdbtoolsservice.edit_data.contracts import EditCell


class EditRowState(Enum):
    CLEAN = 0
    DIRTY_INSERT = 1
    DIRTY_DELETE = 2
    DIRTY_UPDATE = 3


class EditRow:
    """
    A way to return a row in a result set that is being edited. It contains state about whether
    or not the row is dirty
    """

    @property
    def is_dirty(self):
        return self.state is not EditRowState.CLEAN

    def __init__(
        self, row_id: int, cells: list[EditCell], state: EditRowState = EditRowState.CLEAN
    ):
        self.cells = cells
        self.id = row_id
        self.state: EditRowState = state
