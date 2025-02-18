# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test text.py"""

import unittest

from ossdbtoolsservice.language.text import TextUtilities
from ossdbtoolsservice.workspace.contracts import Position, Range  # noqa


class TestTextUtilities(unittest.TestCase):
    """Methods for testing text utility functions"""

    def test_next_delim_not_found(self):
        """Should return length of line if delim does not exist"""
        line = "01 34textnospace"
        start_cols = [3, 5, len(line) - 1]
        for col in start_cols:
            pos = TextUtilities.next_delimiter_pos(line, col)
            self.assertEqual(pos, len(line))

    def test_next_delim_found(self):
        """Should return length of line if delim does not exist"""
        line = "01 345\t789\na/cd"
        start_col_to_delim: dict = {
            0: 2,
            3: 6,
            4: 6,
            8: 10,
            10: 10,  # when cursor is on a delimiter, return it as the next delimiter
            12: 12,  # '/'
            13: 15,  # 'c' -> end of line
        }
        for start, expected_col in start_col_to_delim.items():
            pos = TextUtilities.next_delimiter_pos(line, start)
            self.assertEqual(
                pos,
                expected_col,
                f'For start {start} with value "{line[start]}" '
                f"expected {expected_col} actual {pos}",
            )

    def test_prev_delim_not_found(self):
        """Should return 0 if delim does not exist"""
        line = "0123456789"
        start_cols = [0, 1, 5, len(line) - 1]
        for col in start_cols:
            pos = TextUtilities.prev_delimiter_pos(line, col)
            self.assertEqual(
                pos, 0, f'For start {col} with value "{line[col]}" expected {0} actual {pos}'
            )

    def test_prev_delim_found(self):
        """Should return 0 if on first word or the first index
        after the delimiter for all others"""
        line = "01 345\t789\na/cd"
        start_col_to_delim: dict = {
            0: 0,
            3: 3,
            4: 3,
            8: 7,
            # when on a cursor that is a delimiter, search for previous delimiter.
            # this is important as otherwise, if at the end of a word the range would be
            # the empty string instead of the previous word
            10: 7,
            11: 11,
            12: 11,  # '/' return previous since its an indent
            13: 13,
        }
        for start, expected_col in start_col_to_delim.items():
            pos = TextUtilities.prev_delimiter_pos(line, start)
            self.assertEqual(
                pos,
                expected_col,
                f'For start {start} with value "{line[start]}" '
                f"expected {expected_col} actual {pos}",
            )

    def test_get_token_range(self):
        """Should return a range around the word"""
        # Given a string with some words
        words = ["create", "table", "T1"]  # indexes: 0-5 7-11 13-14
        line = " ".join(words)
        start_col_to_word: dict = {
            0: 0,
            3: 0,
            6: 0,  # if on space between words, should select previous word
            8: 1,
            10: 1,
            12: 1,  # on space between words, should select previous
            13: 2,  # 'c' -> last indent
            14: 2,
        }

        # When I lookup the word range for a given input
        for start, expected_word_index in start_col_to_word.items():
            expected_word = words[expected_word_index]
            expected_line = 2
            pos = Position.from_data(2, start)
            text_range: Range = TextUtilities.get_token_range(pos, line)

            # Then I expect the line value to always match the Positions line
            self.assertEqual(text_range.start.line, expected_line)
            self.assertEqual(text_range.end.line, expected_line)

            # ... and I expect the word to be the one covered by the indent
            actual_word = line[text_range.start.character : text_range.end.character]
            self.assertEqual(
                actual_word,
                expected_word,
                f'For start {start} expected "{expected_word}" actual "{actual_word}"',
            )  # noqa

    def test_get_text_and_range(self):
        """Should return a word and its range"""
        # Given a string with some words
        words = ["create", "table", "T1"]  # indexes: 0-5 7-11 13-14
        line = " ".join(words)
        start_col_to_word: dict = {
            0: 0,
            3: 0,
            6: 0,  # if on space between words, should select previous word
            8: 1,
            10: 1,
            12: 1,  # on space between words, should select previous
            13: 2,  # 'c' -> last indent
            14: 2,
        }

        # When I lookup the word range for a given input
        for start, expected_word_index in start_col_to_word.items():
            expected_word = words[expected_word_index]
            expected_line = 2
            pos = Position.from_data(2, start)
            (actual_word, text_range) = TextUtilities.get_text_and_range(pos, line)

            # Then I expect the line value to always match the Positions line
            self.assertEqual(text_range.start.line, expected_line)
            self.assertEqual(text_range.end.line, expected_line)

            # ... and I expect the word to be the one covered by the indent
            self.assertEqual(
                actual_word,
                expected_word,
                f'For start {start} expected "{expected_word}" actual "{actual_word}"',
            )  # noqa
