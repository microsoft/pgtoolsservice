# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest

from ostoolsservice.workspace.contracts import Position, Range, TextDocumentChangeEvent
from ostoolsservice.workspace.workspace import ScriptFile


class TestScriptFile(unittest.TestCase):
    # INIT TESTS ###########################################################

    def test_init_all_params(self):
        # If: I create a script file with all the parameters provided
        uri = 'file_uri'
        buffer = 'buffer'
        path = 'file_path'
        sf = ScriptFile(uri, buffer, path)

        # Then: The state should be setup with all the provided values
        self.assertEqual(sf._file_uri, uri)
        self.assertEqual(sf.file_uri, uri)
        self.assertEqual(sf._file_path, path)
        self.assertEqual(sf.file_path, path)
        self.assertListEqual(sf._file_lines, [buffer])
        self.assertListEqual(sf.file_lines, [buffer])

    def test_init_most_params(self):
        # If: I create a script file with all the parameters provided
        uri = 'file_uri'
        buffer = 'buffer'
        sf = ScriptFile(uri, buffer, None)

        # Then: The state should be setup with all the provided values
        self.assertEqual(sf._file_uri, uri)
        self.assertEqual(sf.file_uri, uri)
        self.assertIsNone(sf._file_path)
        self.assertIsNone(sf.file_path)
        self.assertListEqual(sf._file_lines, [buffer])
        self.assertListEqual(sf.file_lines, [buffer])

    def test_init_missing_params(self):
        for value in [None, '', '  \t\t\r\n\r\n']:
            with self.assertRaises(ValueError):
                # If: I create a script file while missing a file_uri
                # Then: I expect it to raise an exception
                ScriptFile(value, 'buffer', None)

        with self.assertRaises(ValueError):
            # If: I create a script file while missing a initial buffer
            ScriptFile('file_uri', None, None)

    # GET LINE TESTS #######################################################
    def test_get_line_valid(self):
        # Setup: Create a script file with a selection of test text
        sf = ScriptFile('uri', 'abc\r\ndef\r\nghij\r\nklm', None)

        # If: I ask for a valid line
        # Then: I should get that line w/o new lines
        self.assertEqual(sf.get_line(0), 'abc')
        self.assertEqual(sf.get_line(1), 'def')
        self.assertEqual(sf.get_line(3), 'klm')

    def test_get_line_invalid(self):
        # Setup: Create a script file with a selection of test text
        sf = self._get_test_script_file()

        for line in [-100, -1, 4, 100]:
            with self.assertRaises(ValueError):
                # If: I ask for an invalid line
                # Then: I should get an exception
                sf.get_line(line)

    # GET LINES IN RANGE TESTS #############################################

    def test_get_lines_in_range_valid(self):
        # Setup: Create a script file with a selection of test text
        sf = self._get_test_script_file()

        # If: I ask for the valid lines of the file
        params = Range.from_data(1, 1, 3, 1)
        result = sf.get_lines_in_range(params)

        # Then: I should get a set of lines with the expected result
        expected_result = ['ef', 'ghij', 'k']
        self.assertEqual(result, expected_result)

    def test_get_lines_in_range_invalid_start(self):
        # Setup: Create a script file with a selection of test text
        sf = self._get_test_script_file()

        with self.assertRaises(ValueError):
            # If: I ask for the lines of a file that have an invalid start
            # Then: I should get an exception
            params = Range.from_data(-1, 200, 2, 3)
            sf.get_lines_in_range(params)

    def test_get_lines_in_range_invalid_end(self):
        # Setup: Create a script file with a selection of test text
        sf = self._get_test_script_file()

        with self.assertRaises(ValueError):
            # If: I ask for the lines of a file that have an invalid end
            # Then: I should get an exception
            params = Range.from_data(1, 1, 300, 3000)
            sf.get_lines_in_range(params)

    # GET TEXT IN RANGE TESTS ##############################################

    def test_get_text_in_range(self):
        # Setup: Create a script file with a selection of test text
        sf = self._get_test_script_file()

        # If: I ask for the valid lines of the file
        params = Range.from_data(1, 1, 3, 1)
        result = sf.get_text_in_range(params)

        # Then: I should get a set of lines with the expected result
        expected_result = os.linesep.join(['ef', 'ghij', 'k'])
        self.assertEqual(result, expected_result)

    def test_get_text_in_range_start_of_line(self):
        """Test that get_text_in_range works when the cursor is at the start of a line"""
        sf = self._get_test_script_file()

        # If I get text from a range that covers the entire first line and ends on the second line before any text
        params = Range.from_data(0, 0, 1, 0)
        result = sf.get_text_in_range(params)

        # Then I should get the first line and a line with no content as the result
        expected_result = os.linesep.join(['abc', ''])
        self.assertEqual(result, expected_result)

    # VALIDATE POSITION TESTS ##############################################

    def test_validate_position_valid(self):
        # Setup: Create a script file with a selection of test text
        sf = self._get_test_script_file()

        # If: I validate a valid position
        # Then: It should complete successfully
        sf.validate_position(Position.from_data(2, 1))

    def test_validate_position_invalid_line(self):
        # Setup: Create a script file with a selection of test text
        sf = self._get_test_script_file()

        # If: I validate an invalid line
        for line in [-100, -1, 4, 400]:
            with self.assertRaises(ValueError):
                sf.validate_position(Position.from_data(line, 1))

    def test_validate_position_invalid_col(self):
        # Setup: Create a script file with a selection of test text
        sf = self._get_test_script_file()

        # If: I validate an invalid col
        for col in [-100, -1, 5, 400]:
            with self.assertRaises(ValueError):
                sf.validate_position(Position.from_data(2, col))

    def test_validate_position_end_of_line(self):
        """Test that the column that would add a character to a line is treated as a valid column"""
        # Set up the script file
        script_file = self._get_test_script_file()

        # If I validate the column that would add a character to the end of a line
        # Then no error should be raised
        script_file.validate_position(Position.from_data(2, 4))

    # APPLY CHANGES TESTS ##################################################

    def test_apply_change_invalid_position(self):
        # Setup: Create a script file with a selection of test text
        sf = self._get_test_script_file()

        # If: I apply a change at an invalid part of the document
        # Then:
        # ... I should get an exception throws
        with self.assertRaises(ValueError):
            params = TextDocumentChangeEvent.from_dict({
                'range': {
                    'start': {'line': 1, 'character': -1},      # Invalid character
                    'end': {'line': 3, 'character': 1}
                },
                'text': ''
            })
            sf.apply_change(params)

        # ... The text should remain the same
        self.assertListEqual(sf.file_lines, self._get_test_script_file().file_lines)

    def test_apply_change_replace(self):
        # Setup: Create a script file with a selection of test text
        sf = self._get_test_script_file()

        # If: I apply a change that replaces the text
        params = TextDocumentChangeEvent.from_dict({
            'range': {
                'start': {'line': 1, 'character': 1},
                'end': {'line': 3, 'character': 1}
            },
            'text': '12\r\n3456\r\n78'
        })
        sf.apply_change(params)

        # Then:
        # ... The text should have updated
        expected_result = [
            'abc',
            'd12',
            '3456',
            '78lm'
        ]
        self.assertListEqual(sf.file_lines, expected_result)

    def test_apply_change_remove(self):
        # Setup: Create a script file with a selection of test text
        sf = self._get_test_script_file()

        # If: I apply a change that removes the text
        params = TextDocumentChangeEvent.from_dict({
            'range': {
                'start': {'line': 1, 'character': 1},
                'end': {'line': 3, 'character': 1}
            },
            'text': '1'
        })
        sf.apply_change(params)

        # Then:
        # ... The text should have updated
        expected_result = [
            'abc',
            'd1lm'
        ]
        self.assertListEqual(sf.file_lines, expected_result)

    def test_apply_change_add(self):
        # Setup: Create a script file with a selection of test text
        sf = self._get_test_script_file()

        # If: I apply a change that adds text
        params = TextDocumentChangeEvent.from_dict({
            'range': {
                'start': {'line': 1, 'character': 1},
                'end': {'line': 3, 'character': 1}
            },
            'text': '\r\npgsql\r\nis\r\nawesome\r\n'
        })
        sf.apply_change(params)

        # Then:
        # ... The text should have updated
        expected_result = [
            'abc',
            'd',
            'pgsql',
            'is',
            'awesome',
            'lm'
        ]
        self.assertListEqual(sf.file_lines, expected_result)

    def test_apply_change_add_character(self):
        """Test applying a change by adding a single character to the end of an existing line"""
        # Set up the test file and parameters to add a character at the end of the first line
        script_file = self._get_test_script_file()

        # If I add a single character to the end of a line
        params = TextDocumentChangeEvent.from_dict({
            'range': {
                'start': {'line': 0, 'character': 3},
                'end': {'line': 0, 'character': 3}
            },
            'text': 'a'
        })
        script_file.apply_change(params)

        # Then the text should have updated without a validation error
        expected_result = ['abca', 'def', 'ghij', 'klm']
        self.assertListEqual(script_file.file_lines, expected_result)

    def test_apply_change_add_parentheses(self):
        """Test applying a change that simulates typing parentheses and putting text between them"""
        # Set up the test file and parameters to add a character at the end of the first line
        script_file = self._get_test_script_file()

        # If I add parentheses to the end of a line...
        params = TextDocumentChangeEvent.from_dict({
            'range': {
                'start': {'line': 0, 'character': 3},
                'end': {'line': 0, 'character': 3}
            },
            'text': '()'
        })
        script_file.apply_change(params)

        expected_result = ['abc()', 'def', 'ghij', 'klm']
        self.assertListEqual(script_file.file_lines, expected_result)

        # And then type inside the parentheses
        params = TextDocumentChangeEvent.from_dict({
            'range': {
                'start': {'line': 0, 'character': 4},
                'end': {'line': 0, 'character': 4}
            },
            'text': 'a'
        })
        script_file.apply_change(params)

        expected_result = ['abc(a)', 'def', 'ghij', 'klm']
        self.assertListEqual(script_file.file_lines, expected_result)

        # And then overwrite the last parenthesis
        params = TextDocumentChangeEvent.from_dict({
            'range': {
                'start': {'line': 0, 'character': 5},
                'end': {'line': 0, 'character': 6}
            },
            'text': ')'
        })
        script_file.apply_change(params)

        # Then the text should have updated without a validation error
        expected_result = ['abc(a)', 'def', 'ghij', 'klm']
        self.assertListEqual(script_file.file_lines, expected_result)

    def test_apply_change_remove_across_line(self):
        """Test removing an entire line from the script file by selecting across the line"""
        # Set up the test file and parameters to remove a line from the file
        script_file = self._get_test_script_file()

        # If I remove a line from the file
        params = TextDocumentChangeEvent.from_dict({
            'range': {
                'start': {'line': 0, 'character': 3},
                'end': {'line': 2, 'character': 0}
            },
            'text': ''
        })
        script_file.apply_change(params)

        # Then the text should have updated without a validation error
        expected_result = ['abcghij', 'klm']
        self.assertListEqual(script_file.file_lines, expected_result)

    def test_apply_change_remove_line(self):
        """Test removing an entire line from the script file by selecting the line"""
        # Set up the test file and parameters to remove a line from the file
        script_file = self._get_test_script_file()

        # If I remove a line from the file
        params = TextDocumentChangeEvent.from_dict({
            'range': {
                'start': {'line': 1, 'character': 0},
                'end': {'line': 2, 'character': 0}
            },
            'text': ''
        })
        script_file.apply_change(params)

        # Then the text should have updated without a validation error
        expected_result = ['abc', 'ghij', 'klm']
        self.assertListEqual(script_file.file_lines, expected_result)

    # SET FILE CONTENTS TESTS ##############################################

    def test_set_file_contents(self):
        # If: I set the contents of a script file
        sf = ScriptFile('uri', '', None)
        sf._set_file_contents('line 1\r\n  line 2\n  line 3  ')

        # Then: I should get the expected output lines
        expected_output = [
            'line 1',
            '  line 2',
            '  line 3  '
        ]
        self.assertListEqual(sf.file_lines, expected_output)
        self.assertListEqual(sf._file_lines, expected_output)

    def test_set_file_contents_empty(self):
        # If: I set the contents of a script file to empty
        sf = ScriptFile('uri', '', None)
        sf._set_file_contents('')

        # Then: I should expect a single, empty line in the file lines
        self.assertListEqual(sf.file_lines, [''])
        self.assertListEqual(sf._file_lines, [''])

    # IMPLEMENTATION DETAILS ###############################################

    @staticmethod
    def _get_test_script_file() -> ScriptFile:
        return ScriptFile('uri', 'abc\r\ndef\r\nghij\r\nklm', None)
