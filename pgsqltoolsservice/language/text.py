# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Utility functions for operating with text"""
from typing import Tuple, Set

import pgsqltoolsservice.utils as utils
from pgsqltoolsservice.workspace.contracts.common import Position, Range


class TextUtilities:
    """Utility functions for operating with text"""

    char_delimiters: Set[str] = set([
        ' ',
        '\t',
        '\n',
        '.',
        '+',
        '-',
        '*',
        '>',
        '<',
        '=',
        '/',
        '%',
        ',',
        ';',
        '(',
        ')'
    ])

    @classmethod
    def is_char_delimiter(cls, char: str):
        """Looks up a character in the list of known delimiters"""
        return char in TextUtilities.char_delimiters

    @classmethod
    def next_delimiter_pos(cls, line: str, start_col: int) -> int:
        """
        Gets the column index for the delimiter after the start column,
        or the line length if none found on this line
        """
        length = len(line)
        if length == 0:
            return 0

        utils.validate.is_within_range('start_col', start_col, 0, length)
        index = start_col
        while index < length:
            if TextUtilities.is_char_delimiter(line[index]):
                return index
            index += 1
        # Not found: return the length
        return length

    @classmethod
    def prev_delimiter_pos(cls, line: str, start_col: int) -> int:
        """
        Gets the column index for the delimiter before the start column,
        or 0 if none found on this line
        """
        length = len(line)
        if length == 0:
            return 0

        utils.validate.is_within_range('start_col', start_col, 0, length)
        index = start_col
        if index == length or (index > 0 and TextUtilities.is_char_delimiter(line[index])):
            # If at the end of a line, skip to previous character to begin searching
            # If the current index is a delimiter, go back one since we need to capture the
            # context of the word. We are essentially "to the left" of that delimiter
            index -= 1
        while index > 0:
            if TextUtilities.is_char_delimiter(line[index]):
                # found an index so return the first character after it
                return index + 1
            index -= 1
        # Not found: return the length
        return 0

    @classmethod
    def get_token_range(cls, pos: Position, current_line: str) -> Range:
        """
        Given a position in a field and the current lines text, creates a range
        defining the token to be processed
        """
        row: int = pos.line
        start_col: int = TextUtilities.prev_delimiter_pos(current_line, pos.character)
        end_col: int = TextUtilities.next_delimiter_pos(current_line, pos.character)
        return Range.from_data(row, start_col, row, end_col)

    @classmethod
    def get_text_and_range(cls, pos: Position, current_line: str) -> Tuple[str, Range]:
        """
        Given a position in a field and the current lines text, gets the token representing
        the nearest word
        """
        start_col: int = TextUtilities.prev_delimiter_pos(current_line, pos.character)
        end_col: int = TextUtilities.next_delimiter_pos(current_line, pos.character)
        if end_col > start_col:
            text = current_line[start_col:end_col]
            text_range = Range.from_data(pos.line, start_col, pos.line, end_col)
            return (text, text_range)
        else:
            return ('', None)

    @classmethod
    def get_word(self, text, position):
        words = text.split()
        characters = -1
        for word in words:
            characters += len(word)
            if characters >= position:
                return word
