# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from parameterized import parameterized
import unittest

from ossdbtoolsservice.language.completion.packages.parseutils.utils import find_prev_keyword

class TestParseUtils(unittest.TestCase):
    """Methods for testing ParseUtils"""

    def test_find_prev_keyword_using(self):
        q = 'select * from tbl1 inner join tbl2 using (col1, '
        kw, q2 = find_prev_keyword(q)
        self.assertEqual(kw.value, '(')
        self.assertEqual(q2, 'select * from tbl1 inner join tbl2 using (')

    @parameterized.expand([
        'select * from foo where bar',
        'select * from foo where bar = 1 and baz or ',
        'select * from foo where bar = 1 and baz between qux and ',
    ])
    def test_find_prev_keyword_where(self, sql):
        kw, stripped = find_prev_keyword(sql)
        self.assertEqual(kw.value, 'where')
        self.assertEqual(stripped, 'select * from foo where')

    @parameterized.expand([
        'create table foo (bar int, baz ',
        'select * from foo() as bar (baz '
    ])
    def test_find_prev_keyword_open_parens(self, sql):
        kw, _ = find_prev_keyword(sql)
        self.assertEqual(kw.value, '(')
