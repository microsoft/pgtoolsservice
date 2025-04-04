# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from parameterized import parameterized

from ossdbtoolsservice.language.completion.packages.parseutils.tables import extract_tables
from ossdbtoolsservice.language.completion.packages.parseutils.utils import (
    find_prev_keyword,
    is_open_quote,
)


class TestParseUtils(unittest.TestCase):
    """Methods for testing ParseUtils"""

    def test_empty_string(self):
        tables = extract_tables("")
        self.assertTupleEqual(tables, ())

    def test_simple_select_single_table(self):
        tables = extract_tables("select * from abc")
        self.assertTupleEqual(tables, ((None, "abc", None, False),))

    @parameterized.expand(
        [
            'select * from "abc"."def"',
            'select * from abc."def"',
        ]
    )
    def test_simple_select_single_table_schema_qualified_quoted_table(self, sql):
        tables = extract_tables(sql)
        self.assertTupleEqual(tables, (("abc", "def", '"def"', False),))

    @parameterized.expand(
        [
            "select * from abc.def",
            'select * from "abc".def',
        ]
    )
    def test_simple_select_single_table_schema_qualified(self, sql):
        tables = extract_tables(sql)
        self.assertTupleEqual(tables, (("abc", "def", None, False),))

    def test_simple_select_single_table_double_quoted(self):
        tables = extract_tables('select * from "Abc"')
        self.assertTupleEqual(tables, ((None, "Abc", None, False),))

    def test_simple_select_multiple_tables(self):
        tables = extract_tables("select * from abc, def")
        self.assertSetEqual(
            set(tables), set([(None, "abc", None, False), (None, "def", None, False)])
        )

    def test_simple_select_multiple_tables_double_quoted(self):
        tables = extract_tables('select * from "Abc", "Def"')
        self.assertSetEqual(
            set(tables), set([(None, "Abc", None, False), (None, "Def", None, False)])
        )

    def test_simple_select_single_table_deouble_quoted_aliased(self):
        tables = extract_tables('select * from "Abc" a')
        self.assertTupleEqual(tables, ((None, "Abc", "a", False),))

    def test_simple_select_multiple_tables_deouble_quoted_aliased(self):
        tables = extract_tables('select * from "Abc" a, "Def" d')
        self.assertSetEqual(
            set(tables), set([(None, "Abc", "a", False), (None, "Def", "d", False)])
        )

    def test_simple_select_multiple_tables_schema_qualified(self):
        tables = extract_tables("select * from abc.def, ghi.jkl")
        self.assertSetEqual(
            set(tables), set([("abc", "def", None, False), ("ghi", "jkl", None, False)])
        )

    def test_simple_select_with_cols_single_table(self):
        tables = extract_tables("select a,b from abc")
        self.assertTupleEqual(tables, ((None, "abc", None, False),))

    def test_simple_select_with_cols_single_table_schema_qualified(self):
        tables = extract_tables("select a,b from abc.def")
        self.assertTupleEqual(tables, (("abc", "def", None, False),))

    def test_simple_select_with_cols_multiple_tables(self):
        tables = extract_tables("select a,b from abc, def")
        self.assertSetEqual(
            set(tables), set([(None, "abc", None, False), (None, "def", None, False)])
        )

    def test_simple_select_with_cols_multiple_qualified_tables(self):
        tables = extract_tables("select a,b from abc.def, def.ghi")
        self.assertSetEqual(
            set(tables), set([("abc", "def", None, False), ("def", "ghi", None, False)])
        )

    def test_select_with_hanging_comma_single_table(self):
        tables = extract_tables("select a, from abc")
        self.assertTupleEqual(tables, ((None, "abc", None, False),))

    def test_select_with_hanging_comma_multiple_tables(self):
        tables = extract_tables("select a, from abc, def")
        self.assertSetEqual(
            set(tables), set([(None, "abc", None, False), (None, "def", None, False)])
        )

    def test_select_with_hanging_period_multiple_tables(self):
        tables = extract_tables("SELECT t1. FROM tabl1 t1, tabl2 t2")
        self.assertSetEqual(
            set(tables), set([(None, "tabl1", "t1", False), (None, "tabl2", "t2", False)])
        )

    def test_simple_insert_single_table(self):
        tables = extract_tables('insert into abc (id, name) values (1, "def")')

        # sqlparse mistakenly assigns an alias to the table
        # AND mistakenly identifies the field list as
        # assert tables == ((None, 'abc', 'abc', False),)
        self.assertTupleEqual(tables, ((None, "abc", "abc", False),))

    # TODO nosetest doesn't honor expectedFailure
    # @unittest.expectedFailure
    # def test_simple_insert_single_table_schema_qualified(self):
    #     tables = extract_tables(
    #         'insert into abc.def (id, name) values (1, "def")')
    #     self.assertTupleEqual(tables, ('abc', 'def', None, False),)

    def test_simple_update_table_no_schema(self):
        tables = extract_tables("update abc set id = 1")
        self.assertTupleEqual(tables, ((None, "abc", None, False),))

    def test_simple_update_table_with_schema(self):
        tables = extract_tables("update abc.def set id = 1")
        self.assertTupleEqual(tables, (("abc", "def", None, False),))

    @parameterized.expand(["", "INNER", "LEFT", "RIGHT OUTER"])
    def test_join_table(self, join_type):
        sql = f"SELECT * FROM abc a {join_type} JOIN def d ON a.id = d.num"
        tables = extract_tables(sql)
        self.assertSetEqual(
            set(tables), set([(None, "abc", "a", False), (None, "def", "d", False)])
        )

    def test_join_table_schema_qualified(self):
        tables = extract_tables("SELECT * FROM abc.def x JOIN ghi.jkl y ON x.id = y.num")
        self.assertSetEqual(
            set(tables), set([("abc", "def", "x", False), ("ghi", "jkl", "y", False)])
        )

    def test_incomplete_join_clause(self):
        sql = """select a.x, b.y
                from abc a join bcd b
                on a.id = """
        tables = extract_tables(sql)
        self.assertTupleEqual(tables, ((None, "abc", "a", False), (None, "bcd", "b", False)))

    def test_join_as_table(self):
        tables = extract_tables("SELECT * FROM my_table AS m WHERE m.a > 5")
        self.assertTupleEqual(tables, ((None, "my_table", "m", False),))

    def test_multiple_joins(self):
        sql = """select * from t1
                inner join t2 ON
                t1.id = t2.t1_id
                inner join t3 ON
                t2.id = t3."""
        tables = extract_tables(sql)
        self.assertTupleEqual(
            tables,
            ((None, "t1", None, False), (None, "t2", None, False), (None, "t3", None, False)),
        )

    def test_subselect_tables(self):
        sql = "SELECT * FROM (SELECT  FROM abc"
        tables = extract_tables(sql)
        self.assertTupleEqual(tables, ((None, "abc", None, False),))

    @parameterized.expand(["SELECT * FROM foo.", "SELECT 123 AS foo"])
    def test_extract_no_tables(self, text):
        tables = extract_tables(text)
        self.assertTupleEqual(tables, tuple())

    @parameterized.expand(["", "arg1", "arg1, arg2, arg3"])
    def test_simple_function_as_table(self, arg_list):
        tables = extract_tables(f"SELECT * FROM foo({arg_list})")
        self.assertTupleEqual(tables, ((None, "foo", None, True),))

    @parameterized.expand(["", "arg1", "arg1, arg2, arg3"])
    def test_simple_schema_qualified_function_as_table(self, arg_list):
        tables = extract_tables(f"SELECT * FROM foo.bar({arg_list})")
        self.assertTupleEqual(tables, (("foo", "bar", None, True),))

    @parameterized.expand(["", "arg1", "arg1, arg2, arg3"])
    def test_simple_aliased_function_as_table(self, arg_list):
        tables = extract_tables(f"SELECT * FROM foo({arg_list}) bar")
        self.assertTupleEqual(tables, ((None, "foo", "bar", True),))

    def test_simple_table_and_function(self):
        tables = extract_tables("SELECT * FROM foo JOIN bar()")
        self.assertSetEqual(
            set(tables), set([(None, "foo", None, False), (None, "bar", None, True)])
        )

    def test_complex_table_and_function(self):
        tables = extract_tables("""SELECT * FROM foo.bar baz
                                JOIN bar.qux(x, y, z) quux""")
        self.assertSetEqual(
            set(tables), set([("foo", "bar", "baz", False), ("bar", "qux", "quux", True)])
        )

    def test_find_prev_keyword_using(self):
        q = "select * from tbl1 inner join tbl2 using (col1, "
        kw, q2 = find_prev_keyword(q)
        self.assertEqual(kw.value, "(")
        self.assertEqual(q2, "select * from tbl1 inner join tbl2 using (")

    @parameterized.expand(
        [
            "select * from foo where bar",
            "select * from foo where bar = 1 and baz or ",
            "select * from foo where bar = 1 and baz between qux and ",
        ]
    )
    def test_find_prev_keyword_where(self, sql):
        kw, stripped = find_prev_keyword(sql)
        self.assertEqual(kw.value, "where")
        self.assertEqual(stripped, "select * from foo where")

    @parameterized.expand(
        ["create table foo (bar int, baz ", "select * from foo() as bar (baz "]
    )
    def test_find_prev_keyword_open_parens(self, sql):
        kw, _ = find_prev_keyword(sql)
        self.assertEqual(kw.value, "(")

    @parameterized.expand(
        [
            "",
            "$$ foo $$",
            "$$ 'foo' $$",
            '$$ "foo" $$',
            "$$ $a$ $$",
            "$a$ $$ $a$",
            "foo bar $$ baz $$",
        ]
    )
    def test_is_open_quote__closed(self, sql):
        self.assertFalse(is_open_quote(sql))

    @parameterized.expand(
        [
            "$$",
            ";;;$$",
            "foo $$ bar $$; foo $$",
            "$$ foo $a$",
            "foo 'bar baz",
            "$a$ foo ",
            '$$ "foo" ',
            "$$ $a$ ",
            "foo bar $$ baz",
        ]
    )
    def test_is_open_quote__open(self, sql):
        self.assertTrue(is_open_quote(sql))
