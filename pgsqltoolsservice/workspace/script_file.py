# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from typing import List

from pgsqltoolsservice.utils import validate
from pgsqltoolsservice.workspace.contracts import BufferPosition, BufferRange, FileChange


class FileChange:
    """
    Contains details relating to a content change in an open file
    """
    def __init__(self, string: str, start_line: int, start_column: int, end_line: int, end_column: int):
        self.insert_string: str = string
        self.start_line: int = start_line
        self.start_column: int = start_column
        self.end_line: int = end_line
        self.end_column: int = end_column


class ScriptFile:
    """
    Contains the details and contents of an open script file
    """

    # CONSTRUCTORS #########################################################
    def __init__(self, file_path, client_file_path, initial_buffer):
        """
        Creates a new ScriptFile instance with the specified file contents
        :param file_path: 
        :param client_file_path: 
        :param initial_buffer: 
        """
        self._file_path = file_path
        self._client_file_path = client_file_path

        # Store the initial contents of the file
        self._file_lines = None
        self._set_file_contents(initial_buffer)

    # PROPERTIES ###########################################################
    @property
    def client_file_path(self):
        """
        :return string: Path which the editor client uses to identify this file
        """
        return self._client_file_path

    @property
    def file_lines(self):
        """
        :return list[string]: List of strings for each line of the file 
        """
        return self._file_lines

    @property
    def file_path(self):
        """
        :return string: Path at which this file resides 
        """
        return self._file_path

    @property
    def id(self):
        """
        :return string: A unique string that identifies this file. At this time, this property returns a normalized 
        version of the value stored in the file_path attribute.
        """
        return self._file_path.lower()

    @property
    def is_in_memory(self):
        """
        :return bool: Whether this file is in-memory or not (either unsaved or non-file content) 
        """
        return self._is_in_memory

    # METHODS ##############################################################

    def apply_change(self, file_change: FileChange) -> None:
        """
        Applies the provided file change to the file's contents
        :param FileChange file_change: The change to apply to the file's contents
        """
        # Validate the positions of the file change
        self._validate_position_data(file_change.line, file_change.offset)
        self._validate_position_data(file_change.end_line, file_change.end_offset)

        # Break up the change lines
        change_lines = file_change.insert_string.split('\n')

        # Get the first fragment of the first line that will remain
        first_line_fragment = self.file_lines[file_change.line - 1][:file_change.offset]

        # Get the last fragment of the last line that will remain
        last_line_fragment = self.file_lines[file_change.end_line - 1][file_change.end_offset - 1:]

        # Remove the old lines (by repeatedly removing the first line of the change)
        for i in range(0, file_change.end_line - file_change.line + 1):
            del self.file_lines[file_change.line]

        # Build and insert the new lines
        current_line_number = file_change.line
        for change_index in range(0, len(change_lines)):
            # Since we split the lines above using \n make sure to trim any trailing \r's
            final_line = change_lines[change_index].rstrip(['\r'])

            # Should we add first or last line fragments?
            if change_index == 0:
                final_line = first_line_fragment + final_line
            if change_index == len(change_lines) - 1:
                final_line = last_line_fragment + last_line_fragment

            self.file_lines.insert(current_line_number - 1, final_line)
            current_line_number += 1

    def get_line(self, line: int) -> str:
        """
        Gets a line from the file's contents.
        :param int line: The 1-based line number in the file 
        :return: The complete line at the given line number
        """
        # Validate line is within range of the file
        # TODO: Validate logic is correct
        if line < 1 or line > len(self.file_lines):
            # TODO: Localize
            raise ValueError(u"Line number must be greater than 0 and less than or equal to the number of lines")

        return self.file_lines[line - 1]

    def get_offset_at_position(self, line_number: int, column_number: int) -> int:
        """
        Calculates the zero-based character offset of a given line and column position in the file
        :param line_number: 1-based line number from which the offset is calculated
        :param column_number: 1-based column number from which the offset is calculated 
        :return: 0-based offset for the given file position 
        """
        validate.is_within_range('line_number', line_number, 1, len(self.file_lines))
        validate.is_greater_than('column_number', column_number, 0)

        offset = 0

        for i in range(0, line_number):
            if i == line_number - 1:
                # Subtract 1 to account for 1-based column numbering
                offset += column_number - 1
            else:
                # Add an offset to account for the current platform's newline characters
                # TODO: Wouldn't this blow up if you were editing DOS line endings on Linux?
                offset += len(self.file_lines[i]) + len(os.linesep)

        return offset

    def get_text_in_range(self, buffer_range: BufferRange) -> str:
        """
        Gets the text under a specific range joined with environment-specific newlines
        :param buffer_range: The range to retrieve 
        :return: The text within the specified range with environment-specific newlines
        """
        return os.linesep.join(self.get_lines_in_range(buffer_range))

    def get_lines_in_range(self, buffer_range: BufferRange) -> List[str]:
        """
        Gets a range of lines from the file's contents.
        :param buffer_range: The buffer range from which lines will be extracted 
        :return: A list of strings from the specified range of the file 
        """
        # Validate range
        self.validate_position(buffer_range.start)
        self.validate_position(buffer_range.end)

        output = []
        for line in range(buffer_range.start.line, buffer_range.end.line + 1):
            current_line = self.file_lines[line - 1]

            # If the line we're looking at is not the beginning or end, select entire line,
            # otherwise, trim the unselected part of the line
            start_column = buffer_range.start.column if line == buffer_range.start.line else 1
            end_column = buffer_range.end.column if line == buffer_range.end.line else len(current_line) + 1

            output.append(current_line[start_column-1:end_column+1])
        return output

    def validate_position(self, position: BufferPosition) -> None:
        """
        Raises ValueError if the given position is outside of the file's buffer extents
        :param BufferPosition position: The position in the buffer to be be validated
        """
        self._validate_position_data(position.line, position.column)

    # IMPLEMENTATION DETAILS ###############################################
    def _validate_position_data(self, line: int, column: int) -> None:
        """
        Raises ValueError if the given position is outside of the file's buffer extents
        :param int line: The 1-based line to be validated
        :param int column: The 1-based column to be validated
        """
        # Validate against number of lines
        if line < 1 or line > len(self.file_lines) + 1:
            # TODO: Localize
            raise ValueError(u"Position is outside of file line range")

        # The maximum column is either one past the length of the string or 1 if the string is empty
        line_string = self.file_lines[line - 1]
        max_column = max(len(line_string), 1)

        # Validate against number of columns
        if column < 1 or column > max_column:
            # TODO: Localize
            raise ValueError(u"Position is outside of column range for line {}".format(line))

    def _set_file_contents(self, file_contents: str) -> None:
        """
        Set the script file's contents
        :param file_contents: New contents for the file 
        """
        self._file_lines = [x.rstrip('\r') for x in file_contents.split('\n')]
