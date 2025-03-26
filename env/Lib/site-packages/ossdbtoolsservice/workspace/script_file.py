# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from typing import Optional

from ossdbtoolsservice.utils import validate
from ossdbtoolsservice.workspace.contracts import Position, Range, TextDocumentChangeEvent


class ScriptFile:
    """
    Contains the details and contents of an open script file
    """

    # CONSTRUCTORS #########################################################
    def __init__(self, file_uri: str, initial_buffer: str, file_path: Optional[str]) -> None:
        """
        Creates a new ScriptFile instance with the specified file contents
        :param file_uri: URI for the file provided by the client
        :param initial_buffer: The initial contents of the script file
        :param file_path: Path to the file on disk, if it could be resolved
        """
        # Validate the incoming variables
        validate.is_not_none_or_whitespace("file_uri", file_uri)
        validate.is_not_none("initial_buffer", initial_buffer)

        self._file_uri: str = file_uri
        self._file_path: Optional[str] = file_path

        # Store the initial contents of the file
        self._file_lines: list[str] = []
        self._set_file_contents(initial_buffer)

    # PROPERTIES ###########################################################
    @property
    def file_uri(self) -> str:
        """
        :return: URI of the file as provided by the client
        """
        return self._file_uri

    @property
    def file_lines(self) -> list[str]:
        """
        :return: List of strings for each line of the file
        """
        return self._file_lines

    @property
    def file_path(self) -> Optional[str]:
        """
        :return: Path to the file path on disk, if it exists
        """
        return self._file_path

    # METHODS ##############################################################

    def apply_change(self, file_change: TextDocumentChangeEvent) -> None:
        """
        Applies the provided file change to the file's contents
        :param FileChange file_change: The change to apply to the file's contents
        """
        # Validate the positions of the file change
        if file_change.range is None:
            raise ValueError("File change range must be set")

        start = file_change.range.start
        end = file_change.range.end
        if start is None or end is None:
            raise ValueError("File change range must have start and end positions")
        self.validate_position(start)
        self.validate_position(end)

        # Break up the change lines
        change_lines: list[str] = (
            file_change.text.split("\n") if file_change.text is not None else []
        )

        # Get the first fragment of the first line that will remain
        first_line_fragment: str = self.file_lines[start.line][: start.character]

        # Get the last fragment of the last line that will remain
        last_line_fragment: str = self.file_lines[end.line][end.character :]

        # Remove the old lines (by repeatedly removing the first line of the change)
        for _i in range(0, end.line - start.line + 1):
            del self.file_lines[start.line]

        # Build and insert the new lines
        current_line_number: int = start.line
        for change_index in range(0, len(change_lines)):
            # Since we split the lines above using \n make sure to trim any trailing \r's
            final_line: str = change_lines[change_index].rstrip("\r")

            # Should we add first or last line fragments?
            if change_index == 0:
                final_line = first_line_fragment + final_line
            if change_index == len(change_lines) - 1:
                final_line = final_line + last_line_fragment

            self.file_lines.insert(current_line_number, final_line)
            current_line_number += 1

    def get_line(self, line: int) -> str:
        """
        Gets a line from the file's contents.
        :param int line: The 0-based line number in the file
        :return: The complete line at the given line number
        """
        # Validate line is within range of the file
        validate.is_within_range("line", line, 0, len(self._file_lines) - 1)
        return self.file_lines[line]

    def get_text_in_range(self, buffer_range: Range | None) -> str:
        """
        Gets the text under a specific range joined with environment-specific newlines
        :param buffer_range: The range to retrieve
        :return: The text within the specified range with environment-specific newlines
        """
        return os.linesep.join(self.get_lines_in_range(buffer_range))

    def get_lines_in_range(self, buffer_range: Range | None) -> list[str]:
        """
        Gets a range of lines from the file's contents.
        :param buffer_range: The buffer range from which lines will be extracted
        :return: A list of strings from the specified range of the file
        """
        if buffer_range is None:
            return []

        start = buffer_range.start
        end = buffer_range.end
        if start is None or end is None:
            return []

        # Validate range
        self.validate_position(start)
        self.validate_position(end)

        output: list[str] = []
        for line in range(start.line, end.line + 1):
            current_line: str = self.file_lines[line]

            # If the line we're looking at is not the beginning or end, select entire line,
            # otherwise, trim the unselected part of the line
            start_column: int = start.character if line == start.line else 0
            end_column: int = end.character if line == end.line else len(current_line)

            output.append(current_line[start_column:end_column])
        return output

    def get_all_text(self) -> str:
        """Gets all the text from the file, joined with environment-specific newlines"""
        return os.linesep.join(self.file_lines)

    def validate_position(self, position: Position) -> None:
        """
        Raises ValueError if the given position is outside of the file's buffer extents
        :param BufferPosition position: The position in the buffer to be be validated
        """
        # Validate against number of lines
        if position.line < 0 or position.line >= len(self.file_lines):
            # TODO: Localize
            raise ValueError("Position is outside of file line range")

        # Retrieve the line of the position
        line_string: str = self.file_lines[position.line]

        # Validate against number of columns.
        # Allow the character to be in the last column to add a
        # character to the end of the line.
        if position.character < 0 or position.character > len(line_string):
            # TODO: Localize
            raise ValueError(f"Position is outside of column range for line {position.line}")

    # IMPLEMENTATION DETAILS ###############################################

    def _set_file_contents(self, file_contents: str) -> None:
        """
        Set the script file's contents
        :param file_contents: New contents for the file
        """
        self._file_lines = [x.rstrip("\r") for x in file_contents.split("\n")]
