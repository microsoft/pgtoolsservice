# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from enum import Enum
from pgsqltoolsservice.edit_data.contracts import EditCell
from typing import List


class EditRowState(Enum):
    Clean = 0
    DirtyInsert = 1
    DirtyDelete = 2
    DirtyUpdate = 3


class EditRow:
    '''
    A way to return a row in a result set that is being edited. It contains state about whether
    or not the row is dirty
    '''

    @property
    def is_dirty(self):
        return self.state is not EditRowState.Clean

    def __init__(self, row_id: int, cells: List[EditCell], state: EditRowState= EditRowState.Clean):
        self.cells = cells
        self.id = row_id
        self.state: EditRowState = state
