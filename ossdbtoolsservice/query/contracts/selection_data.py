# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.core.models import PGTSBaseModel
from ossdbtoolsservice.hosting import OutgoingMessageRegistration
from ossdbtoolsservice.workspace.contracts import Position, Range


class SelectionData(PGTSBaseModel):
    """Container class for a selection range from file"""

    start_line: int = 0
    start_column: int = 0
    end_line: int = 0
    end_column: int = 0

    def to_range(self) -> Range:
        """Convert the SelectionData object to a workspace service Range object"""
        return Range(
            Position(self.start_line, self.start_column),
            Position(self.end_line, self.end_column),
        )


OutgoingMessageRegistration.register_outgoing_message(SelectionData)
