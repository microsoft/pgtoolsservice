# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test text.py"""

from typing import List
import unittest

from ossdbtoolsservice.language.contracts import (
    CompletionItem, CompletionItemKind
)
from ossdbtoolsservice.language.keywords import DefaultCompletionHelper
from ossdbtoolsservice.workspace.contracts import (
    Range
)


class TestCompletionHelper(unittest.TestCase):
    """Methods for testing text utility functions"""

    def test_is_keyword_match(self):
        """Test keyword lookup"""
        # Given a default completion helper
        helper = DefaultCompletionHelper()
        # When I look up a known keyword
        is_key = helper.is_keyword('create')
        # Then I expect the keyword to be found
        self.assertTrue(is_key)

    def test_is_keyword_miss(self):
        """Test keyword lookup"""
        # Given a default completion helper
        helper = DefaultCompletionHelper()
        # When I look up a random word
        is_key = helper.is_keyword('notakeyword')
        # Then I expect the keyword to be missed
        self.assertFalse(is_key)

    def test_get_matches_emptystr(self):
        """Test get matches on empty string"""
        # Given a default completion helper
        helper = DefaultCompletionHelper()
        # When I match the empty string
        matches: List[CompletionItem] = helper.get_matches('', None, False)
        # Then I expect no keywords to be returned
        self.assertEqual([], matches)

    def test_get_matches_one_char(self):
        """Test get matches on 1 character range"""
        # Given a default completion helper
        helper = DefaultCompletionHelper()
        text_range = Range.from_data(1, 1, 1, 2)
        start = 'c'
        # When I match 'c'
        matches: List[CompletionItem] = helper.get_matches(start, text_range, False)
        # Then I expect keywords starting with c to be returned
        self.assertTrue(len(matches) > 0)
        # ... and I expect words to be uppercased
        self.verify_match('CREATE', matches, text_range)
        # ... and I expect keywords starting in d to be skipped
        self.verify_miss('DELETE', matches)

        # and When I match with lowercase
        matches: List[CompletionItem] = helper.get_matches(start, text_range, True)
        # then I expect a lowercase result
        self.verify_match('create', matches, text_range)
        self.verify_miss('CREATE', matches)

    def test_get_matches_full_keyword(self):
        """Test get matches on a keyword"""
        # Given a default completion helper
        helper = DefaultCompletionHelper()
        text_range = Range.from_data(1, 1, 1, 2)
        start = 'create'
        # When I match 'create'
        matches: List[CompletionItem] = helper.get_matches(start, text_range, False)
        # Then I expect only 1 match
        self.assertEqual(1, len(matches))
        # ... and I expect words to be uppercased
        self.verify_match('CREATE', matches, text_range)

    def verify_match(self, word: str, matches: List[CompletionItem], text_range: Range):
        """Verifies match against its label and other properties"""
        match: CompletionItem = next(iter(obj for obj in matches if obj.label == word), None)
        self.assertIsNotNone(match)
        self.assertEqual(word, match.label)
        self.assertEqual(CompletionItemKind.Keyword, match.kind)
        self.assertEqual(word, match.insert_text_format)
        self.assertEqual(text_range, match.text_edit.range)
        self.assertEqual(word, match.text_edit.new_text)

    def verify_miss(self, word: str, matches: List[CompletionItem]):
        match = next(iter(obj for obj in matches if obj.label == word), None)
        self.assertIsNone(match)
