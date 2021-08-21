# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import Mock

from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document

from ossdbtoolsservice.language.completion.pgcompleter import PGCompleter
from tests.language.completion.metadata import compare_result_and_correct_result


class TestNaiveCompletion(unittest.TestCase):
    """Methods for testing non-smart completion"""

    def setUp(self):
        self.completer = PGCompleter(smart_completion=False)
        self.complete_event = Mock()

    def test_empty_string_completion(self):
        text = ''
        position = 0
        result = self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event)
        correct_result = list(map(Completion, self.completer.all_completions))
        compare_result_and_correct_result(self, result, correct_result)

    def test_select_keyword_completion(self):
        text = 'SEL'
        position = len('SEL')
        result = self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event)

        self.assertEqual(result, [Completion(text='SELECT', start_position=-3)])

    def test_function_name_completion(self):
        text = 'SELECT MA'
        position = len('SELECT MA')
        result = self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event)

        self.assertIn(Completion(text="MATERIALIZED VIEW", start_position=-2), result)
        self.assertIn(Completion(text="MAX", start_position=-2), result)
        self.assertIn(Completion(text="MAXEXTENTS", start_position=-2), result)

    def test_column_name_completion(self):
        text = 'SELECT  FROM users'
        position = len('SELECT ')
        result = self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event)
        correct_result = list(map(Completion, self.completer.all_completions))
        compare_result_and_correct_result(self, result, correct_result)

    # {{ PGToolsService EDIT }}
    # Disabling as we will not support cli-only features
    # def test_paths_completion(self):
    #     text = '\i '
    #     position = len(text)
    #     result = set(self.completer.get_completions(
    #         Document(text=text, cursor_position=position),
    #         self.complete_event,
    #         smart_completion=True))
    #     # Set comparison: > means "is superset"
    #     self.assertTrue(result > set([Completion(text="setup.py", start_position=0)]))

    def test_alter_well_known_keywords_completion(self):
        text = 'ALTER '
        position = len(text)
        result = self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event,
            smart_completion=True)
        self.assertIn(Completion(text="DATABASE", display_meta='keyword'), result)
        self.assertIn(Completion(text="TABLE", display_meta='keyword'), result)
        self.assertIn(Completion(text="SYSTEM", display_meta='keyword'), result)
        self.assertTrue(Completion(text="CREATE", display_meta="keyword") not in result)

    def test_keyword_lower_casing(self):
        new_completer = PGCompleter(smart_completion=True, settings={'keyword_casing': 'lower'})
        text = 'SEL'
        position = len(text)
        result = new_completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event)

        # then completions should now be lower case
        self.assertEqual(result, [Completion(text='select', start_position=-3, display_meta="keyword")])

    def test_keyword_upper_casing(self):
        new_completer = PGCompleter(smart_completion=True, settings={'keyword_casing': 'upper'})
        text = 'sel'
        position = len(text)
        result = new_completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event)

        # then completions should now be lower case
        self.assertEqual(result, [Completion(text='SELECT', start_position=-3, display_meta="keyword")])

    def test_keyword_auto_casing(self):
        new_completer = PGCompleter(smart_completion=True, settings={'keyword_casing': 'auto'})

        # if text is lower case
        text = 'sel'
        position = len(text)
        result = new_completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event)

        # then completions should be lower case as well
        self.assertEqual(result, [Completion(text='select', start_position=-3, display_meta="keyword")])
