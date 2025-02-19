# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.hosting import OutgoingMessageRegistration
from ossdbtoolsservice.serialization import Serializable
from ossdbtoolsservice.workspace.contracts import Position, Range


class SelectionData(Serializable):
    """Container class for a selection range from file"""

    start_line: int
    start_column: int
    end_line: int
    end_column: int

    def __init__(
        self,
        start_line: int = 0,
        start_column: int = 0,
        end_line: int = 0,
        end_column: int = 0,
    ):
        self.start_line: int = start_line
        self.start_column: int = start_column
        self.end_line: int = end_line
        self.end_column: int = end_column

    def to_range(self) -> Range:
        """Convert the SelectionData object to a workspace service Range object"""
        return Range(
            Position(self.start_line, self.start_column),
            Position(self.end_line, self.end_column),
        )


OutgoingMessageRegistration.register_outgoing_message(SelectionData)
