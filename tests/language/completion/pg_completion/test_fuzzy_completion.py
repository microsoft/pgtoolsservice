# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from parameterized import parameterized, param
import unittest

from ossdbtoolsservice.language.completion.pg_completer import PGCompleter


class TestFuzzyCompletion(unittest.TestCase):
    """Methods for testing fuzzy completion"""

    def setUp(self):
        self.completer = PGCompleter()

    def test_ranking_ignores_identifier_quotes(self):
        """When calculating result rank, identifier quotes should be ignored.

        The result ranking algorithm ignores identifier quotes. Without this
        correction, the match "user", which Postgres requires to be quoted
        since it is also a reserved word, would incorrectly fall below the
        match user_action because the literal quotation marks in "user"
        alter the position of the match.

        This test checks that the fuzzy ranking algorithm correctly ignores
        quotation marks when computing match ranks.

        """

        text = 'user'
        collection = ['user_action', '"user"']
        matches = self.completer.find_matches(text, collection)
        self.assertEqual(len(matches), 2)

    def test_ranking_based_on_shortest_match(self):
        """Fuzzy result rank should be based on shortest match.

        Result ranking in fuzzy searching is partially based on the length
        of matches: shorter matches are considered more relevant than
        longer ones. When searching for the text 'user', the length
        component of the match 'user_group' could be either 4 ('user') or
        7 ('user_gr').

        This test checks that the fuzzy ranking algorithm uses the shorter
        match when calculating result rank.

        """
        text = 'user'
        collection = ['api_user', 'user_group']
        matches = self.completer.find_matches(text, collection)
        self.assertGreater(matches[1].priority, matches[0].priority)

    @parameterized.expand([
        param(['user_action', 'user']),
        param(['user_group', 'user']),
        param(['user_group', 'user_action']),
    ])
    def test_should_break_ties_using_lexical_order(self, collection):
        """Fuzzy result rank should use lexical order to break ties.

        When fuzzy matching, if multiple matches have the same match length and
        start position, present them in lexical (rather than arbitrary) order. For
        example, if we have tables 'user', 'user_action', and 'user_group', a
        search for the text 'user' should present these tables in this order.

        The input collections to this test are out of order; each run checks that
        the search text 'user' results in the input tables being reordered
        lexically.

        """
        text = 'user'
        matches = self.completer.find_matches(text, collection)
        self.assertGreater(matches[1].priority, matches[0].priority)

    def test_matching_should_be_case_insensitive(self):
        """Fuzzy matching should keep matches even if letter casing doesn't match.

        This test checks that variations of the text which have different casing
        are still matched.
        """
        text = 'foo'
        collection = ['Foo', 'FOO', 'fOO']
        matches = self.completer.find_matches(text, collection)
        self.assertEqual(len(matches), 3)
