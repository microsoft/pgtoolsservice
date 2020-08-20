# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from parameterized import parameterized
from sqlparse import parse

from ossdbtoolsservice.language.completion.packages.parseutils.pg_utils.ctes import \
    extract_column_names as _extract_column_names
from ossdbtoolsservice.language.completion.packages.parseutils.pg_utils.ctes import (
    extract_ctes, token_start_pos)


def extract_column_names(sql):
    p = parse(sql)[0]
    return _extract_column_names(p)


class TestCTEs(unittest.TestCase):
    """Methods for testing CTE Processing"""

    def test_token_str_pos(self):
        sql = 'SELECT * FROM xxx'
        p = parse(sql)[0]
        idx = p.token_index(p.tokens[-1])
        self.assertEqual(token_start_pos(p.tokens, idx), len('SELECT * FROM '))

        sql = 'SELECT * FROM \nxxx'
        p = parse(sql)[0]
        idx = p.token_index(p.tokens[-1])
        self.assertEqual(token_start_pos(p.tokens, idx),
                         len('SELECT * FROM \n'))

    def test_single_column_name_extraction(self):
        sql = 'SELECT abc FROM xxx'
        self.assertTupleEqual(extract_column_names(sql), ('abc',))

    def test_aliased_single_column_name_extraction(self):
        sql = 'SELECT abc def FROM xxx'
        self.assertTupleEqual(extract_column_names(sql), ('def',))

    def test_aliased_expression_name_extraction(self):
        sql = 'SELECT 99 abc FROM xxx'
        self.assertTupleEqual(extract_column_names(sql), ('abc',))

    def test_multiple_column_name_extraction(self):
        sql = 'SELECT abc, def FROM xxx'
        self.assertTupleEqual(extract_column_names(sql), ('abc', 'def'))

    def test_missing_column_name_handled_gracefully(self):
        sql = 'SELECT abc, 99 FROM xxx'
        self.assertTupleEqual(extract_column_names(sql), ('abc',))

        sql = 'SELECT abc, 99, def FROM xxx'
        self.assertTupleEqual(extract_column_names(sql), ('abc', 'def'))

    def test_aliased_multiple_column_name_extraction(self):
        sql = 'SELECT abc def, ghi jkl FROM xxx'
        self.assertTupleEqual(extract_column_names(sql), ('def', 'jkl'))

    def test_table_qualified_column_name_extraction(self):
        sql = 'SELECT abc.def, ghi.jkl FROM xxx'
        self.assertTupleEqual(extract_column_names(sql), ('def', 'jkl'))

    @parameterized.expand([
        'INSERT INTO foo (x, y, z) VALUES (5, 6, 7) RETURNING x, y',
        'DELETE FROM foo WHERE x > y RETURNING x, y',
        'UPDATE foo SET x = 9 RETURNING x, y',
    ])
    def test_extract_column_names_from_returning_clause(self, sql):
        self.assertTupleEqual(extract_column_names(sql), ('x', 'y'))

    def test_simple_cte_extraction(self):
        sql = 'WITH a AS (SELECT abc FROM xxx) SELECT * FROM a'
        start_pos = len('WITH a AS ')
        stop_pos = len('WITH a AS (SELECT abc FROM xxx)')
        ctes, remainder = extract_ctes(sql)

        # Verify CTE returns table name, columns, start and end position
        self.assertTupleEqual(
            tuple(ctes), (('a', ('abc',), start_pos, stop_pos),))
        self.assertEqual(remainder.strip(), 'SELECT * FROM a')

    def test_cte_extraction_around_comments(self):
        sql = '''--blah blah blah
                WITH a AS (SELECT abc def FROM x)
                SELECT * FROM a'''
        start_pos = len('''--blah blah blah
                WITH a AS ''')
        stop_pos = len('''--blah blah blah
                WITH a AS (SELECT abc def FROM x)''')

        ctes, remainder = extract_ctes(sql)
        self.assertTupleEqual(
            tuple(ctes), (('a', ('def',), start_pos, stop_pos),))
        self.assertEqual(remainder.strip(), 'SELECT * FROM a')

    def test_multiple_cte_extraction(self):
        sql = '''WITH
                x AS (SELECT abc, def FROM x),
                y AS (SELECT ghi, jkl FROM y)
                SELECT * FROM a, b'''

        start1 = len('''WITH
                x AS ''')

        stop1 = len('''WITH
                x AS (SELECT abc, def FROM x)''')

        start2 = len('''WITH
                x AS (SELECT abc, def FROM x),
                y AS ''')

        stop2 = len('''WITH
                x AS (SELECT abc, def FROM x),
                y AS (SELECT ghi, jkl FROM y)''')

        ctes, remainder = extract_ctes(sql)
        self.assertTupleEqual(ctes[0], ('x', ('abc', 'def'), start1, stop1))
        self.assertTupleEqual(ctes[1], ('y', ('ghi', 'jkl'), start2, stop2))
