# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import os
from typing import List

from pgsqltoolsservice.workspace.contracts import Position, Range, TextDocumentChangeEvent
import pgsqltoolsservice.utils as utils


class ScriptFile:
    """
    Contains the details and contents of an open script file
    """

    # CONSTRUCTORS #########################################################
    def __init__(self, file_path, client_file_path, initial_buffer):
        """
        Creates a new ScriptFile instance with the specified file contents
        :param file_path: The path at which the script file resides
        :param client_file_path: The path which the client uses to identify the file
        :param initial_buffer: The initial contents of the script file
        """
        self._file_path = file_path
        self._client_file_path = client_file_path

        # Store the initial contents of the file
        self._file_lines = None
        self._set_file_contents(initial_buffer)

    # PROPERTIES ###########################################################
    @property
    def client_file_path(self) -> str:
        """
        :return: Path which the editor client uses to identify this file
        """
        return self._client_file_path

    @property
    def file_lines(self) -> List[str]:
        """
        :return: List of strings for each line of the file
        """
        return self._file_lines

    @property
    def file_path(self) -> str:
        """
        :return: Path at which this file resides
        """
        return self._file_path

    @property
    def id(self) -> str:
        """
        :return: A unique string that identifies this file. At this time, this property returns a normalized
        version of the value stored in the file_path attribute.
        """
        # TODO: Validate that this works with OSs that have case-sensitive filesystems (ie, Linux)
        return self._file_path.lower()

    # METHODS ##############################################################

    def apply_change(self, file_change: TextDocumentChangeEvent) -> None:
        """
        Applies the provided file change to the file's contents
        :param FileChange file_change: The change to apply to the file's contents
        """
        # Validate the positions of the file change
        self.validate_position(file_change.range.start)
        self.validate_position(file_change.range.end)

        # Break up the change lines
        change_lines: List[str] = file_change.text.split('\n')

        # Get the first fragment of the first line that will remain
        first_line_fragment: str = self.file_lines[file_change.range.start.line][:file_change.range.start.character]

        # Get the last fragment of the last line that will remain
        # TODO: Verify that the +0 is correct here.
        last_line_fragment: str = self.file_lines[file_change.range.end.line][file_change.range.end.character:]

        # Remove the old lines (by repeatedly removing the first line of the change)
        for i in range(0, file_change.range.end.line - file_change.range.start.line + 1):
            del self.file_lines[file_change.range.start.line]

        # Build and insert the new lines
        current_line_number: int = file_change.range.start.line
        for change_index in range(0, len(change_lines)):
            # Since we split the lines above using \n make sure to trim any trailing \r's
            final_line: str = change_lines[change_index].rstrip('\r')

            # Should we add first or last line fragments?
            if change_index == 0:
                final_line = first_line_fragment + final_line
            if change_index == len(change_lines) - 1:
                final_line = final_line + last_line_fragment

            self.file_lines.insert(current_line_number + change_index, final_line)
        logger = logging.getLogger('pgsqltoolsservice')
        utils.log.log_debug(logger, 'New file contents: {}'.format('\n'.join(self.file_lines)))

    def get_line(self, line: int) -> str:
        """
        Gets a line from the file's contents.
        :param int line: The 0-based line number in the file
        :return: The complete line at the given line number
        """
        # Validate line is within range of the file
        utils.validate.is_within_range('line', line, 0, len(self._file_lines) - 1)
        return self.file_lines[line]

    def get_text_in_range(self, buffer_range: Range) -> str:
        """
        Gets the text under a specific range joined with environment-specific newlines
        :param buffer_range: The range to retrieve
        :return: The text within the specified range with environment-specific newlines
        """
        return os.linesep.join(self.get_lines_in_range(buffer_range))

    def get_lines_in_range(self, buffer_range: Range) -> List[str]:
        """
        Gets a range of lines from the file's contents.
        :param buffer_range: The buffer range from which lines will be extracted
        :return: A list of strings from the specified range of the file
        """
        # Validate range
        self.validate_position(buffer_range.start)
        self.validate_position(buffer_range.end)

        output: List[str] = []
        for line in range(buffer_range.start.line, buffer_range.end.line + 1):
            current_line: str = self.file_lines[line]

            # If the line we're looking at is not the beginning or end, select entire line,
            # otherwise, trim the unselected part of the line
            start_column: int = buffer_range.start.character if line == buffer_range.start.line else 0
            end_column: int = buffer_range.end.character + 1 if line == buffer_range.end.line else len(current_line)

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
        if position.line < 0 or position.line > len(self.file_lines):
            # TODO: Localize
            raise ValueError('Position is outside of file line range')

        # Retrieve the line of the position
        line_string: str = self.file_lines[position.line]

        # Validate against number of columns
        if position.character < 0 or position.character > len(line_string):
            # TODO: Localize
            raise ValueError('Position is outside of column range for line {}'.format(position.line))

    # IMPLEMENTATION DETAILS ###############################################

    def _set_file_contents(self, file_contents: str) -> None:
        """
        Set the script file's contents
        :param file_contents: New contents for the file
        """
        self._file_lines = [x.rstrip('\r') for x in file_contents.split('\n')]
