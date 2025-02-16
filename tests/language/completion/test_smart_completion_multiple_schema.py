# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import itertools
import unittest

from parameterized import param, parameterized

from tests.language.completion.metadata import (
    MetaData,
    alias,
    column,
    fk_join,
    function,
    get_result,
    join,
    name_join,
    no_qual,
    qual,
    result_set,
    schema,
    table,
    wildcard_expansion,
)

METADATA = {
    "tables": {
        "public": {
            "users": ["id", "email", "first_name", "last_name"],
            "orders": ["id", "ordered_date", "status", "datestamp"],
            "select": ["id", "localtime", "ABC"],
        },
        "custom": {
            "users": ["id", "phone_number"],
            "Users": ["userid", "username"],
            "products": ["id", "product_name", "price"],
            "shipments": ["id", "address", "user_id"],
        },
        "Custom": {"projects": ["projectid", "name"]},
        "blog": {
            "entries": ["entryid", "entrytitle", "entrytext"],
            "tags": ["tagid", "name"],
            "entrytags": ["entryid", "tagid"],
            "entacclog": ["entryid", "username", "datestamp"],
        },
    },
    "functions": {
        "public": [
            ["func1", [], [], [], "", False, False, False],
            ["func2", [], [], [], "", False, False, False],
        ],
        "custom": [
            ["func3", [], [], [], "", False, False, False],
            ["set_returning_func", ["x"], ["integer"], ["o"], "integer", False, False, True],
        ],
        "Custom": [["func4", [], [], [], "", False, False, False]],
        "blog": [
            [
                "extract_entry_symbols",
                ["_entryid", "symbol"],
                ["integer", "text"],
                ["i", "o"],
                "",
                False,
                False,
                True,
            ],
            [
                "enter_entry",
                ["_title", "_text", "entryid"],
                ["text", "text", "integer"],
                ["i", "i", "o"],
                "",
                False,
                False,
                False,
            ],
        ],
    },
    "datatypes": {
        "public": ["typ1", "typ2"],
        "custom": ["typ3", "typ4"],
    },
    "foreignkeys": {
        "custom": [("public", "users", "id", "custom", "shipments", "user_id")],
        "blog": [
            ("blog", "entries", "entryid", "blog", "entacclog", "entryid"),
            ("blog", "entries", "entryid", "blog", "entrytags", "entryid"),
            ("blog", "tags", "tagid", "blog", "entrytags", "tagid"),
        ],
    },
    "defaults": {
        "public": {
            ("orders", "id"): "nextval('orders_id_seq'::regclass)",
            ("orders", "datestamp"): "now()",
            ("orders", "status"): "'PENDING'::text",
        }
    },
}

TESTDATA = MetaData(METADATA)
CASED_SCHEMAS = [schema(x) for x in ("public", "blog", "CUSTOM", '"Custom"')]
CASING = (
    "SELECT",
    "Orders",
    "User_Emails",
    "CUSTOM",
    "Func1",
    "Entries",
    "Tags",
    "EntryTags",
    "EntAccLog",
    "EntryID",
    "EntryTitle",
    "EntryText",
)
completers = TESTDATA.get_completers(CASING)

filteredCompleters = completers(filtr=True, casing=False, qualify=no_qual)


def to_params(completer):
    result = []
    if not isinstance(completer, list):
        completer = [completer]

    for i in completer:
        result.append(param(i))
    return result


class TestSmartCompletionMultipleSchemata(unittest.TestCase):
    """Methods for testing smart completion with multiple schemas"""

    @parameterized.expand(itertools.product(filteredCompleters, ["users", '"users"']))
    def test_suggested_column_names_from_shadowed_visible_table(self, completer, table_name):
        result = result_set(completer, "SELECT  FROM " + table_name, len("SELECT "))
        self.assertSetEqual(result, set(TESTDATA.columns_functions_and_keywords("users")))

    @parameterized.expand(
        itertools.product(
            filteredCompleters,
            [
                "SELECT  from custom.users",
                "WITH users as (SELECT 1 AS foo) SELECT  from custom.users",
            ],
        )
    )
    def test_suggested_column_names_from_qualified_shadowed_table(self, completer, text):
        result = result_set(completer, text, position=text.find("  ") + 1)
        self.assertSetEqual(
            result, set(TESTDATA.columns_functions_and_keywords("users", "custom"))
        )

    @parameterized.expand(
        itertools.product(
            filteredCompleters,
            [
                "WITH users as (SELECT 1 AS foo) SELECT  from users",
            ],
        )
    )
    def test_suggested_column_names_from_cte(self, completer, text):
        result = result_set(completer, text, text.find("  ") + 1)
        self.assertSetEqual(result, set([column("foo")] + TESTDATA.functions_and_keywords()))

    @parameterized.expand(
        itertools.product(
            completers(casing=False),
            [
                "SELECT * FROM users JOIN custom.shipments ON ",
                """SELECT *
        FROM public.users
        JOIN custom.shipments ON """,
            ],
        )
    )
    def test_suggested_join_conditions(self, completer, text):
        result = result_set(completer, text)
        self.assertSetEqual(
            result,
            set(
                [
                    alias("users"),
                    alias("shipments"),
                    name_join("shipments.id = users.id"),
                    fk_join("shipments.user_id = users.id"),
                ]
            ),
        )

    @parameterized.expand(
        itertools.product(
            completers(filtr=True, casing=False, aliasing=False),
            (
                "SELECT * FROM public.{0} RIGHT OUTER JOIN ",
                """SELECT *
        FROM {0}
        JOIN """,
            ),
            ("users", '"users"', "Users"),
        )
    )
    def test_suggested_joins(self, completer, query, tbl):
        result = result_set(completer, query.format(tbl))
        self.assertSetEqual(
            result,
            set(
                TESTDATA.schemas_and_from_clause_items()
                + [join(f"custom.shipments ON shipments.user_id = {tbl}.id")]
            ),
        )

    @parameterized.expand(to_params(filteredCompleters))
    def test_suggested_column_names_from_schema_qualifed_table(self, completer):
        result = result_set(completer, "SELECT  from custom.products", len("SELECT "))
        self.assertSetEqual(
            result, set(TESTDATA.columns_functions_and_keywords("products", "custom"))
        )

    @parameterized.expand(
        itertools.product(
            completers(filtr=True, casing=False),
            [
                "INSERT INTO orders(",
                "INSERT INTO orders (",
                "INSERT INTO public.orders(",
                "INSERT INTO public.orders (",
            ],
        )
    )
    def test_suggested_columns_with_insert(self, completer, text):
        self.assertSetEqual(result_set(completer, text), set(TESTDATA.columns("orders")))

    @parameterized.expand(to_params(filteredCompleters))
    def test_suggested_column_names_in_function(self, completer):
        result = result_set(completer, "SELECT MAX( from custom.products", len("SELECT MAX("))
        self.assertSetEqual(result, set(TESTDATA.columns("products", "custom")))

    @parameterized.expand(
        itertools.product(
            completers(casing=False, aliasing=False),
            [
                "SELECT * FROM Custom.",
                "SELECT * FROM custom.",
                'SELECT * FROM "custom".',
            ],
        )
    )
    def test_suggested_table_names_with_schema_dot(self, completer, text):
        for use_leading_double_quote in [False, True]:
            if use_leading_double_quote:
                text += '"'
                start_position = -1
            else:
                start_position = 0

            result = result_set(completer, text)
            self.assertSetEqual(
                result, set(TESTDATA.from_clause_items("custom", start_position))
            )

    @parameterized.expand(
        itertools.product(
            completers(casing=False, aliasing=False),
            [
                'SELECT * FROM "Custom".',
            ],
            [False, True],
        )
    )
    def test_suggested_table_names_with_schema_dot2(
        self, completer, text, use_leading_double_quote
    ):
        if use_leading_double_quote:
            text += '"'
            start_position = -1
        else:
            start_position = 0

        result = result_set(completer, text)
        self.assertSetEqual(result, set(TESTDATA.from_clause_items("Custom", start_position)))

    @parameterized.expand(to_params(completers(filtr=True, casing=False)))
    def test_suggested_column_names_with_qualified_alias(self, completer):
        result = result_set(completer, "SELECT p. from custom.products p", len("SELECT p."))
        self.assertSetEqual(result, set(TESTDATA.columns("products", "custom")))

    @parameterized.expand(to_params(filteredCompleters))
    def test_suggested_multiple_column_names(self, completer):
        result = result_set(completer, "SELECT id,  from custom.products", len("SELECT id, "))
        self.assertSetEqual(
            result, set(TESTDATA.columns_functions_and_keywords("products", "custom"))
        )

    @parameterized.expand(to_params(completers(filtr=True, casing=False)))
    def test_suggested_multiple_column_names_with_alias(self, completer):
        result = result_set(
            completer, "SELECT p.id, p. from custom.products p", len("SELECT u.id, u.")
        )
        self.assertSetEqual(result, set(TESTDATA.columns("products", "custom")))

    @parameterized.expand(
        itertools.product(
            completers(filtr=True, casing=False),
            [
                "SELECT x.id, y.product_name FROM custom.products x "
                "JOIN custom.products y ON ",
                "SELECT x.id, y.product_name FROM custom.products x "
                "JOIN custom.products y ON JOIN public.orders z ON z.id > y.id",
            ],
        )
    )
    def test_suggestions_after_on(self, completer, text):
        position = len(
            "SELECT x.id, y.product_name FROM custom.products x JOIN custom.products y ON "
        )
        result = result_set(completer, text, position)
        self.assertSetEqual(
            result,
            set(
                [
                    alias("x"),
                    alias("y"),
                    name_join("y.price = x.price"),
                    name_join("y.product_name = x.product_name"),
                    name_join("y.id = x.id"),
                ]
            ),
        )

    @parameterized.expand(to_params(completers()))
    def test_suggested_aliases_after_on_right_side(self, completer):
        text = (
            "SELECT x.id, y.product_name FROM custom.products x "
            "JOIN custom.products y ON x.id = "
        )
        result = result_set(completer, text)
        self.assertSetEqual(result, set([alias("x"), alias("y")]))

    @parameterized.expand(to_params(completers(filtr=True, casing=False, aliasing=False)))
    def test_table_names_after_from(self, completer):
        text = "SELECT * FROM "
        result = result_set(completer, text)
        self.assertSetEqual(result, set(TESTDATA.schemas_and_from_clause_items()))

    @parameterized.expand(to_params(completers(filtr=True, casing=False)))
    def test_schema_qualified_function_name(self, completer):
        text = "SELECT custom.func"
        result = result_set(completer, text)
        self.assertSetEqual(
            result,
            set(
                [
                    function("func3()", -len("func")),
                    function("set_returning_func()", -len("func")),
                ]
            ),
        )

    @parameterized.expand(
        itertools.product(
            completers(filtr=True, casing=False),
            [
                "SELECT 1::custom.",
                "CREATE TABLE foo (bar custom.",
                "CREATE FUNCTION foo (bar INT, baz custom.",
                "ALTER TABLE foo ALTER COLUMN bar TYPE custom.",
            ],
        )
    )
    def test_schema_qualified_type_name(self, completer, text):
        result = result_set(completer, text)
        self.assertSetEqual(result, set(TESTDATA.types("custom")))

    @parameterized.expand(to_params(completers(filtr=True, casing=False)))
    def test_suggest_columns_from_aliased_set_returning_function(self, completer):
        result = result_set(
            completer, "select f. from custom.set_returning_func() f", len("select f.")
        )
        self.assertSetEqual(
            result, set(TESTDATA.columns("set_returning_func", "custom", "functions"))
        )

    @parameterized.expand(
        itertools.product(
            filteredCompleters,
            [
                "SELECT * FROM custom.set_returning_func()",
                "SELECT * FROM Custom.set_returning_func()",
                "SELECT * FROM Custom.Set_Returning_Func()",
            ],
        )
    )
    def test_wildcard_column_expansion_with_function(self, completer, text):
        position = len("SELECT *")

        completions = get_result(completer, text, position)

        col_list = "x"
        expected = [wildcard_expansion(col_list)]

        self.assertListEqual(expected, completions)

    @parameterized.expand(to_params(completers(filtr=True, casing=False)))
    def test_wildcard_column_expansion_with_alias_qualifier(self, completer):
        text = "SELECT p.* FROM custom.products p"
        position = len("SELECT p.*")

        completions = get_result(completer, text, position)

        col_list = "id, p.product_name, p.price"
        expected = [wildcard_expansion(col_list)]

        self.assertListEqual(expected, completions)

    @parameterized.expand(
        itertools.product(
            completers(filtr=True, casing=False),
            [
                """
        SELECT count(1) FROM users;
        CREATE FUNCTION foo(custom.products _products) returns custom.shipments
        LANGUAGE SQL
        AS $foo$
        SELECT 1 FROM custom.shipments;
        INSERT INTO public.orders(*) values(-1, now(), 'preliminary');
        SELECT 2 FROM custom.users;
        $foo$;
        SELECT count(1) FROM custom.shipments;
        """,
                "INSERT INTO public.orders(*",
                "INSERT INTO public.Orders(*",
                "INSERT INTO public.orders (*",
                "INSERT INTO public.Orders (*",
                "INSERT INTO orders(*",
                "INSERT INTO Orders(*",
                "INSERT INTO orders (*",
                "INSERT INTO Orders (*",
                "INSERT INTO public.orders(*)",
                "INSERT INTO public.Orders(*)",
                "INSERT INTO public.orders (*)",
                "INSERT INTO public.Orders (*)",
                "INSERT INTO orders(*)",
                "INSERT INTO Orders(*)",
                "INSERT INTO orders (*)",
                "INSERT INTO Orders (*)",
            ],
        )
    )
    def test_wildcard_column_expansion_with_insert(self, completer, text):
        position = text.index("*") + 1
        completions = get_result(completer, text, position)

        expected = [wildcard_expansion("ordered_date, status")]
        self.assertListEqual(expected, completions)

    @parameterized.expand(to_params(completers(filtr=True, casing=False)))
    def test_wildcard_column_expansion_with_table_qualifier(self, completer):
        text = 'SELECT "select".* FROM public."select"'
        position = len('SELECT "select".*')

        completions = get_result(completer, text, position)

        col_list = 'id, "select"."localtime", "select"."ABC"'
        expected = [wildcard_expansion(col_list)]

        self.assertListEqual(expected, completions)

    @parameterized.expand(to_params(completers(filtr=True, casing=False, qualify=qual)))
    def test_wildcard_column_expansion_with_two_tables(self, completer):
        text = 'SELECT * FROM public."select" JOIN custom.users ON true'
        position = len("SELECT *")

        completions = get_result(completer, text, position)

        cols = (
            '"select".id, "select"."localtime", "select"."ABC", users.id, users.phone_number'
        )
        expected = [wildcard_expansion(cols)]
        self.assertListEqual(expected, completions)

    @parameterized.expand(to_params(completers(filtr=True, casing=False)))
    def test_wildcard_column_expansion_with_two_tables_and_parent(self, completer):
        text = 'SELECT "select".* FROM public."select" JOIN custom.users u ON true'
        position = len('SELECT "select".*')

        completions = get_result(completer, text, position)

        col_list = 'id, "select"."localtime", "select"."ABC"'
        expected = [wildcard_expansion(col_list)]

        self.assertListEqual(expected, completions)

    @parameterized.expand(
        itertools.product(
            completers(filtr=True, casing=False),
            [
                "SELECT U. FROM custom.Users U",
                "SELECT U. FROM custom.USERS U",
                "SELECT U. FROM custom.users U",
                'SELECT U. FROM "custom".Users U',
                'SELECT U. FROM "custom".USERS U',
                'SELECT U. FROM "custom".users U',
            ],
        )
    )
    def test_suggest_columns_from_unquoted_table(self, completer, text):
        position = len("SELECT U.")
        result = result_set(completer, text, position)
        self.assertSetEqual(result, set(TESTDATA.columns("users", "custom")))

    @parameterized.expand(
        itertools.product(
            completers(filtr=True, casing=False),
            ['SELECT U. FROM custom."Users" U', 'SELECT U. FROM "custom"."Users" U'],
        )
    )
    def test_suggest_columns_from_quoted_table(self, completer, text):
        position = len("SELECT U.")
        result = result_set(completer, text, position)
        self.assertSetEqual(result, set(TESTDATA.columns("Users", "custom")))

    texts = ["SELECT * FROM ", "SELECT * FROM public.Orders O CROSS JOIN "]

    @parameterized.expand(
        itertools.product(completers(filtr=True, casing=False, aliasing=False), texts)
    )
    def test_schema_or_visible_table_completion(self, completer, text):
        result = result_set(completer, text)
        self.assertSetEqual(result, set(TESTDATA.schemas_and_from_clause_items()))

    @parameterized.expand(
        itertools.product(completers(aliasing=True, casing=False, filtr=True), texts)
    )
    def test_table_aliases(self, completer, text):
        result = result_set(completer, text)
        self.assertSetEqual(
            result,
            set(
                TESTDATA.schemas()
                + [
                    table("users u"),
                    table("orders o" if text == "SELECT * FROM " else "orders o2"),
                    table('"select" s'),
                    function("func1() f"),
                    function("func2() f"),
                ]
            ),
        )

    @parameterized.expand(
        itertools.product(completers(aliasing=True, casing=True, filtr=True), texts)
    )
    def test_aliases_with_casing(self, completer, text):
        result = result_set(completer, text)
        self.assertSetEqual(
            result,
            set(
                CASED_SCHEMAS
                + [
                    table("users u"),
                    table("Orders O" if text == "SELECT * FROM " else "Orders O2"),
                    table('"select" s'),
                    function("Func1() F"),
                    function("func2() f"),
                ]
            ),
        )

    @parameterized.expand(
        itertools.product(completers(aliasing=False, casing=True, filtr=True), texts)
    )
    def test_table_casing(self, completer, text):
        result = result_set(completer, text)
        self.assertSetEqual(
            result,
            set(
                CASED_SCHEMAS
                + [
                    table("users"),
                    table("Orders"),
                    table('"select"'),
                    function("Func1()"),
                    function("func2()"),
                ]
            ),
        )

    @parameterized.expand(to_params(completers(aliasing=False, casing=True)))
    def test_alias_search_without_aliases2(self, completer):
        text = "SELECT * FROM blog.et"
        result = get_result(completer, text)
        self.assertEqual(result[0], table("EntryTags", -2))

    @parameterized.expand(to_params(completers(aliasing=False, casing=True)))
    def test_alias_search_without_aliases1(self, completer):
        text = "SELECT * FROM blog.e"
        result = get_result(completer, text)
        self.assertEqual(result[0], table("Entries", -1))

    @parameterized.expand(to_params(completers(aliasing=True, casing=True)))
    def test_alias_search_with_aliases2(self, completer):
        text = "SELECT * FROM blog.et"
        result = get_result(completer, text)
        self.assertEqual(result[0], table("EntryTags ET", -2))

    @parameterized.expand(to_params(completers(aliasing=True, casing=True)))
    def test_alias_search_with_aliases1(self, completer):
        text = "SELECT * FROM blog.e"
        result = get_result(completer, text)
        self.assertEqual(result[0], table("Entries E", -1))

    @parameterized.expand(to_params(completers(aliasing=True, casing=True)))
    def test_join_alias_search_with_aliases1(self, completer):
        text = "SELECT * FROM blog.Entries E JOIN blog.e"
        result = get_result(completer, text)
        self.assertListEqual(
            result[:2],
            [table("Entries E2", -1), join("EntAccLog EAL ON EAL.EntryID = E.EntryID", -1)],
        )

    @parameterized.expand(to_params(completers(aliasing=False, casing=True)))
    def test_join_alias_search_without_aliases1(self, completer):
        text = "SELECT * FROM blog.Entries JOIN blog.e"
        result = get_result(completer, text)
        self.assertListEqual(
            result[:2],
            [
                table("Entries", -1),
                join("EntAccLog ON EntAccLog.EntryID = Entries.EntryID", -1),
            ],
        )

    @parameterized.expand(to_params(completers(aliasing=True, casing=True)))
    def test_join_alias_search_with_aliases2(self, completer):
        text = "SELECT * FROM blog.Entries E JOIN blog.et"
        result = get_result(completer, text)
        self.assertEqual(result[0], join("EntryTags ET ON ET.EntryID = E.EntryID", -2))

    @parameterized.expand(to_params(completers(aliasing=False, casing=True)))
    def test_join_alias_search_without_aliases2(self, completer):
        text = "SELECT * FROM blog.Entries JOIN blog.et"
        result = get_result(completer, text)
        self.assertEqual(
            result[0], join("EntryTags ON EntryTags.EntryID = Entries.EntryID", -2)
        )

    @parameterized.expand(to_params(completers()))
    def test_function_alias_search_without_aliases(self, completer):
        text = "SELECT blog.ees"
        result = get_result(completer, text)
        first = result[0]
        self.assertEqual(first.start_position, -3)
        self.assertEqual(first.text, "extract_entry_symbols()")
        self.assertEqual(first.display, "extract_entry_symbols(_entryid)")

    @parameterized.expand(to_params(completers()))
    def test_function_alias_search_with_aliases(self, completer):
        text = "SELECT blog.ee"
        result = get_result(completer, text)
        first = result[0]
        self.assertEqual(first.start_position, -2)
        self.assertEqual(first.text, "enter_entry(_title := , _text := )")
        self.assertEqual(first.display, "enter_entry(_title, _text)")

    @parameterized.expand(to_params(completers(filtr=True, casing=True, qualify=no_qual)))
    def test_column_alias_search(self, completer):
        result = get_result(completer, "SELECT et FROM blog.Entries E", len("SELECT et"))
        cols = ("EntryText", "EntryTitle", "EntryID")
        self.assertListEqual(result[:3], [column(c, -2) for c in cols])

    @parameterized.expand(to_params(completers(casing=True)))
    def test_column_alias_search_qualified(self, completer):
        result = get_result(completer, "SELECT E.ei FROM blog.Entries E", len("SELECT E.ei"))
        cols = ("EntryID", "EntryTitle")
        self.assertListEqual(result[:3], [column(c, -2) for c in cols])

    @parameterized.expand(to_params(completers(casing=False, filtr=False, aliasing=False)))
    def test_schema_object_order(self, completer):
        result = get_result(completer, "SELECT * FROM u")
        self.assertListEqual(
            result[:3],
            [table(t, pos=-1) for t in ("users", 'custom."Users"', "custom.users")],
        )

    @parameterized.expand(to_params(completers(casing=False, filtr=False, aliasing=False)))
    def test_all_schema_objects(self, completer):
        text = "SELECT * FROM "
        result = result_set(completer, text)
        # Note: set comparison >= means is superset
        self.assertTrue(
            result
            >= set(
                [table(x) for x in ("orders", '"select"', "custom.shipments")]
                + [function(x + "()") for x in ("func2", "custom.func3")]
            )
        )

    @parameterized.expand(to_params(completers(filtr=False, aliasing=False, casing=True)))
    def test_all_schema_objects_with_casing(self, completer):
        text = "SELECT * FROM "
        result = result_set(completer, text)
        self.assertTrue(
            result
            >= set(
                [table(x) for x in ("Orders", '"select"', "CUSTOM.shipments")]
                + [function(x + "()") for x in ("func2", "CUSTOM.func3")]
            )
        )

    @parameterized.expand(to_params(completers(casing=False, filtr=False, aliasing=True)))
    def test_all_schema_objects_with_aliases(self, completer):
        text = "SELECT * FROM "
        result = result_set(completer, text)
        self.assertTrue(
            result
            >= set(
                [table(x) for x in ("orders o", '"select" s', "custom.shipments s")]
                + [function(x) for x in ("func2() f", "custom.func3() f")]
            )
        )

    @parameterized.expand(to_params(completers(casing=False, filtr=False, aliasing=True)))
    def test_set_schema(self, completer):
        text = "SET SCHEMA "
        result = result_set(completer, text)
        self.assertSetEqual(
            result,
            set(
                [schema("'blog'"), schema("'Custom'"), schema("'custom'"), schema("'public'")]
            ),
        )
