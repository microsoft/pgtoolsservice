import itertools
import unittest

from parameterized import parameterized

from ossdbtoolsservice.language.completion.packages.mysql_completion_engine import \
    suggest_type


class TestMySQLCompletionEngine(unittest.TestCase):

    def sorted_dicts(self, dicts):
        """input is a list of dicts."""
        return sorted(tuple(x.items()) for x in dicts)

    def test_select_suggests_cols_with_visible_table_scope(self):
        suggestions = suggest_type('SELECT  FROM tabl', 'SELECT ')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'alias', 'aliases': ['tabl']},
            {'type': 'column', 'tables': [(None, 'tabl', None)]},
            {'type': 'function', 'schema': []},
            {'type': 'keyword'},
        ]))

    def test_select_suggests_cols_with_qualified_table_scope(self):
        suggestions = suggest_type('SELECT  FROM sch.tabl', 'SELECT ')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'alias', 'aliases': ['tabl']},
            {'type': 'column', 'tables': [('sch', 'tabl', None)]},
            {'type': 'function', 'schema': []},
            {'type': 'keyword'},
        ]))

    @parameterized.expand([
        'SELECT * FROM tabl WHERE ',
        'SELECT * FROM tabl WHERE (',
        'SELECT * FROM tabl WHERE foo = ',
        'SELECT * FROM tabl WHERE bar OR ',
        'SELECT * FROM tabl WHERE foo = 1 AND ',
        'SELECT * FROM tabl WHERE (bar > 10 AND ',
        'SELECT * FROM tabl WHERE (bar AND (baz OR (qux AND (',
        'SELECT * FROM tabl WHERE 10 < ',
        'SELECT * FROM tabl WHERE foo BETWEEN ',
        'SELECT * FROM tabl WHERE foo BETWEEN foo AND ',
    ])
    def test_where_suggests_columns_functions(self, expression):
        suggestions = suggest_type(expression, expression)
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'alias', 'aliases': ['tabl']},
            {'type': 'column', 'tables': [(None, 'tabl', None)]},
            {'type': 'function', 'schema': []},
            {'type': 'keyword'},
        ]))

    @parameterized.expand([
        'SELECT * FROM tabl WHERE foo IN (',
        'SELECT * FROM tabl WHERE foo IN (bar, ',
    ])
    def test_where_in_suggests_columns(self, expression):
        suggestions = suggest_type(expression, expression)
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'alias', 'aliases': ['tabl']},
            {'type': 'column', 'tables': [(None, 'tabl', None)]},
            {'type': 'function', 'schema': []},
            {'type': 'keyword'},
        ]))

    def test_where_equals_any_suggests_columns_or_keywords(self):
        text = 'SELECT * FROM tabl WHERE foo = ANY('
        suggestions = suggest_type(text, text)
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'alias', 'aliases': ['tabl']},
            {'type': 'column', 'tables': [(None, 'tabl', None)]},
            {'type': 'function', 'schema': []},
            {'type': 'keyword'}]))

    def test_lparen_suggests_cols(self):
        suggestion = suggest_type('SELECT MAX( FROM tbl', 'SELECT MAX(')
        self.assertEqual(suggestion, [
            {'type': 'column', 'tables': [(None, 'tbl', None)]}])

    def test_operand_inside_function_suggests_cols1(self):
        suggestion = suggest_type(
            'SELECT MAX(col1 +  FROM tbl', 'SELECT MAX(col1 + ')
        self.assertEqual(suggestion, [
            {'type': 'column', 'tables': [(None, 'tbl', None)]}])

    def test_operand_inside_function_suggests_cols2(self):
        suggestion = suggest_type(
            'SELECT MAX(col1 + col2 +  FROM tbl', 'SELECT MAX(col1 + col2 + ')
        self.assertEqual(suggestion, [
            {'type': 'column', 'tables': [(None, 'tbl', None)]}])

    def test_select_suggests_cols_and_funcs(self):
        suggestions = suggest_type('SELECT ', 'SELECT ')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'alias', 'aliases': []},
            {'type': 'column', 'tables': []},
            {'type': 'function', 'schema': []},
            {'type': 'keyword'},
        ]))

    @parameterized.expand([
        'SELECT * FROM ',
        'INSERT INTO ',
        'COPY ',
        'UPDATE ',
        'DESCRIBE ',
        'DESC ',
        'EXPLAIN ',
        'SELECT * FROM foo JOIN ',
    ])
    def test_expression_suggests_tables_views_and_schemas(self, expression):
        suggestions = suggest_type(expression, expression)
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'table', 'schema': []},
            {'type': 'view', 'schema': []},
            {'type': 'schema'}]))

    @parameterized.expand([
        'SELECT * FROM sch.',
        'INSERT INTO sch.',
        'COPY sch.',
        'UPDATE sch.',
        'DESCRIBE sch.',
        'DESC sch.',
        'EXPLAIN sch.',
        'SELECT * FROM foo JOIN sch.',
    ])
    def test_expression_suggests_qualified_tables_views_and_schemas(self, expression):
        suggestions = suggest_type(expression, expression)
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'table', 'schema': 'sch'},
            {'type': 'view', 'schema': 'sch'}]))

    def test_truncate_suggests_tables_and_schemas(self):
        suggestions = suggest_type('TRUNCATE ', 'TRUNCATE ')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'table', 'schema': []},
            {'type': 'schema'}]))

    def test_truncate_suggests_qualified_tables(self):
        suggestions = suggest_type('TRUNCATE sch.', 'TRUNCATE sch.')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'table', 'schema': 'sch'}]))

    def test_distinct_suggests_cols(self):
        suggestions = suggest_type('SELECT DISTINCT ', 'SELECT DISTINCT ')
        self.assertEqual(suggestions, [{'type': 'column', 'tables': []}])

    def test_col_comma_suggests_cols(self):
        suggestions = suggest_type('SELECT a, b, FROM tbl', 'SELECT a, b,')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'alias', 'aliases': ['tbl']},
            {'type': 'column', 'tables': [(None, 'tbl', None)]},
            {'type': 'function', 'schema': []},
            {'type': 'keyword'},
        ]))

    def test_table_comma_suggests_tables_and_schemas(self):
        suggestions = suggest_type('SELECT a, b FROM tbl1, ',
                                   'SELECT a, b FROM tbl1, ')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'table', 'schema': []},
            {'type': 'view', 'schema': []},
            {'type': 'schema'}]))

    def test_into_suggests_tables_and_schemas(self):
        suggestion = suggest_type('INSERT INTO ', 'INSERT INTO ')
        self.assertEqual(self.sorted_dicts(suggestion), self.sorted_dicts([
            {'type': 'table', 'schema': []},
            {'type': 'view', 'schema': []},
            {'type': 'schema'}]))

    def test_insert_into_lparen_suggests_cols(self):
        suggestions = suggest_type('INSERT INTO abc (', 'INSERT INTO abc (')
        self.assertEqual(suggestions, [{'type': 'column', 'tables': [(None, 'abc', None)]}])

    def test_insert_into_lparen_partial_text_suggests_cols(self):
        suggestions = suggest_type('INSERT INTO abc (i', 'INSERT INTO abc (i')
        self.assertEqual(suggestions, [{'type': 'column', 'tables': [(None, 'abc', None)]}])

    def test_insert_into_lparen_comma_suggests_cols(self):
        suggestions = suggest_type('INSERT INTO abc (id,', 'INSERT INTO abc (id,')
        self.assertEqual(suggestions, [{'type': 'column', 'tables': [(None, 'abc', None)]}])

    def test_partially_typed_col_name_suggests_col_names(self):
        suggestions = suggest_type('SELECT * FROM tabl WHERE col_n',
                                   'SELECT * FROM tabl WHERE col_n')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'alias', 'aliases': ['tabl']},
            {'type': 'column', 'tables': [(None, 'tabl', None)]},
            {'type': 'function', 'schema': []},
            {'type': 'keyword'},
        ]))

    def test_dot_suggests_cols_of_a_table_or_schema_qualified_table(self):
        suggestions = suggest_type('SELECT tabl. FROM tabl', 'SELECT tabl.')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'column', 'tables': [(None, 'tabl', None)]},
            {'type': 'table', 'schema': 'tabl'},
            {'type': 'view', 'schema': 'tabl'},
            {'type': 'function', 'schema': 'tabl'}]))

    def test_dot_suggests_cols_of_an_alias(self):
        suggestions = suggest_type('SELECT t1. FROM tabl1 t1, tabl2 t2',
                                   'SELECT t1.')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'table', 'schema': 't1'},
            {'type': 'view', 'schema': 't1'},
            {'type': 'column', 'tables': [(None, 'tabl1', 't1')]},
            {'type': 'function', 'schema': 't1'}]))

    def test_dot_col_comma_suggests_cols_or_schema_qualified_table(self):
        suggestions = suggest_type('SELECT t1.a, t2. FROM tabl1 t1, tabl2 t2',
                                   'SELECT t1.a, t2.')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'column', 'tables': [(None, 'tabl2', 't2')]},
            {'type': 'table', 'schema': 't2'},
            {'type': 'view', 'schema': 't2'},
            {'type': 'function', 'schema': 't2'}]))

    @parameterized.expand([
        'SELECT * FROM (',
        'SELECT * FROM foo WHERE EXISTS (',
        'SELECT * FROM foo WHERE bar AND NOT EXISTS (',
        'SELECT 1 AS',
    ])
    def test_sub_select_suggests_keyword(self, expression):
        suggestion = suggest_type(expression, expression)
        self.assertEqual(suggestion, [{'type': 'keyword'}])

    @parameterized.expand([
        'SELECT * FROM (S',
        'SELECT * FROM foo WHERE EXISTS (S',
        'SELECT * FROM foo WHERE bar AND NOT EXISTS (S',
    ])
    def test_sub_select_partial_text_suggests_keyword(self, expression):
        suggestion = suggest_type(expression, expression)
        self.assertEqual(suggestion, [{'type': 'keyword'}])

    def test_outer_table_reference_in_exists_subquery_suggests_columns(self):
        q = 'SELECT * FROM foo f WHERE EXISTS (SELECT 1 FROM bar WHERE f.'
        suggestions = suggest_type(q, q)
        self.assertEqual(suggestions, [
            {'type': 'column', 'tables': [(None, 'foo', 'f')]},
            {'type': 'table', 'schema': 'f'},
            {'type': 'view', 'schema': 'f'},
            {'type': 'function', 'schema': 'f'}])

    @parameterized.expand([
        'SELECT * FROM (SELECT * FROM ',
        'SELECT * FROM foo WHERE EXISTS (SELECT * FROM ',
        'SELECT * FROM foo WHERE bar AND NOT EXISTS (SELECT * FROM ',
    ])
    def test_sub_select_table_name_completion(self, expression):
        suggestion = suggest_type(expression, expression)
        self.assertEqual(self.sorted_dicts(suggestion), self.sorted_dicts([
            {'type': 'table', 'schema': []},
            {'type': 'view', 'schema': []},
            {'type': 'schema'}]))

    def test_sub_select_col_name_completion(self):
        suggestions = suggest_type('SELECT * FROM (SELECT  FROM abc',
                                   'SELECT * FROM (SELECT ')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'alias', 'aliases': ['abc']},
            {'type': 'column', 'tables': [(None, 'abc', None)]},
            {'type': 'function', 'schema': []},
            {'type': 'keyword'},
        ]))

    def test_sub_select_multiple_col_name_completion(self):
        suggestions = suggest_type('SELECT * FROM (SELECT a, FROM abc',
                                   'SELECT * FROM (SELECT a, ')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'column', 'tables': [(None, 'a', None), (None, 'abc', None)]},
            {'type': 'function', 'schema': []},
            {'type': 'alias', 'aliases': ['a', 'abc']},
            {'type': 'keyword'}]))

    def test_sub_select_dot_col_name_completion(self):
        suggestions = suggest_type('SELECT * FROM (SELECT t. FROM tabl t',
                                   'SELECT * FROM (SELECT t.')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'column', 'tables': [(None, 'tabl', 't')]},
            {'type': 'table', 'schema': 't'},
            {'type': 'view', 'schema': 't'},
            {'type': 'function', 'schema': 't'}]))

    @parameterized.expand(itertools.product(['', 'foo'], ['', 'INNER', 'LEFT', 'RIGHT OUTER']))
    def test_join_suggests_tables_and_schemas(self, tbl_alias, join_type):
        text = 'SELECT * FROM abc {0} {1} JOIN '.format(tbl_alias, join_type)
        suggestion = suggest_type(text, text)
        self.assertEqual(self.sorted_dicts(suggestion), self.sorted_dicts([
            {'type': 'table', 'schema': []},
            {'type': 'view', 'schema': []},
            {'type': 'schema'}]))

    @parameterized.expand([
        'SELECT * FROM abc a JOIN def d ON a.',
        'SELECT * FROM abc a JOIN def d ON a.id = d.id AND a.',
    ])
    def test_join_alias_dot_suggests_cols1(self, sql):
        suggestions = suggest_type(sql, sql)
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'column', 'tables': [(None, 'abc', 'a')]},
            {'type': 'table', 'schema': 'a'},
            {'type': 'view', 'schema': 'a'},
            {'type': 'function', 'schema': 'a'}]))

    @parameterized.expand([
        'SELECT * FROM abc a JOIN def d ON a.id = d.',
        'SELECT * FROM abc a JOIN def d ON a.id = d.id AND a.id2 = d.',
    ])
    def test_join_alias_dot_suggests_cols2(self, sql):
        suggestions = suggest_type(sql, sql)
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'column', 'tables': [(None, 'def', 'd')]},
            {'type': 'table', 'schema': 'd'},
            {'type': 'view', 'schema': 'd'},
            {'type': 'function', 'schema': 'd'}]))

    @parameterized.expand([
        'select a.x, b.y from abc a join bcd b on ',
        'select a.x, b.y from abc a join bcd b on a.id = b.id OR ',
    ])
    def test_on_suggests_aliases(self, sql):
        suggestions = suggest_type(sql, sql)
        self.assertEqual(suggestions, [{'type': 'alias', 'aliases': ['a', 'b']}])

    @parameterized.expand([
        'select abc.x, bcd.y from abc join bcd on ',
        'select abc.x, bcd.y from abc join bcd on abc.id = bcd.id AND ',
    ])
    def test_on_suggests_tables(self, sql):
        suggestions = suggest_type(sql, sql)
        self.assertEqual(suggestions, [{'type': 'alias', 'aliases': ['abc', 'bcd']}])

    @parameterized.expand([
        'select a.x, b.y from abc a join bcd b on a.id = ',
        'select a.x, b.y from abc a join bcd b on a.id = b.id AND a.id2 = ',
    ])
    def test_on_suggests_aliases_right_side(self, sql):
        suggestions = suggest_type(sql, sql)
        self.assertEqual(suggestions, [{'type': 'alias', 'aliases': ['a', 'b']}])

    @parameterized.expand([
        'select abc.x, bcd.y from abc join bcd on ',
        'select abc.x, bcd.y from abc join bcd on abc.id = bcd.id and ',
    ])
    def test_on_suggests_tables_right_side(self, sql):
        suggestions = suggest_type(sql, sql)
        self.assertEqual(suggestions, [{'type': 'alias', 'aliases': ['abc', 'bcd']}])

    @parameterized.expand(['', 'col1, '])
    def test_join_using_suggests_common_columns(self, col_list):
        text = 'select * from abc inner join def using (' + col_list
        self.assertEqual(suggest_type(text, text), [
            {'type': 'column',
             'tables': [(None, 'abc', None), (None, 'def', None)],
             'drop_unique': True}])

    def test_2_statements_2nd_current(self):
        suggestions = suggest_type('select * from a; select * from ',
                                   'select * from a; select * from ')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'table', 'schema': []},
            {'type': 'view', 'schema': []},
            {'type': 'schema'}]))

        suggestions = suggest_type('select * from a; select  from b',
                                   'select * from a; select ')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'alias', 'aliases': ['b']},
            {'type': 'column', 'tables': [(None, 'b', None)]},
            {'type': 'function', 'schema': []},
            {'type': 'keyword'},
        ]))

        # Should work even if first statement is invalid
        suggestions = suggest_type('select * from; select * from ',
                                   'select * from; select * from ')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'table', 'schema': []},
            {'type': 'view', 'schema': []},
            {'type': 'schema'}]))

    def test_2_statements_1st_current(self):
        suggestions = suggest_type('select * from ; select * from b',
                                   'select * from ')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'table', 'schema': []},
            {'type': 'view', 'schema': []},
            {'type': 'schema'}]))

        suggestions = suggest_type('select  from a; select * from b',
                                   'select ')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'alias', 'aliases': ['a']},
            {'type': 'column', 'tables': [(None, 'a', None)]},
            {'type': 'function', 'schema': []},
            {'type': 'keyword'},
        ]))

    def test_3_statements_2nd_current(self):
        suggestions = suggest_type('select * from a; select * from ; select * from c',
                                   'select * from a; select * from ')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'table', 'schema': []},
            {'type': 'view', 'schema': []},
            {'type': 'schema'}]))

        suggestions = suggest_type('select * from a; select  from b; select * from c',
                                   'select * from a; select ')
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'alias', 'aliases': ['b']},
            {'type': 'column', 'tables': [(None, 'b', None)]},
            {'type': 'function', 'schema': []},
            {'type': 'keyword'},
        ]))

    def test_create_db_with_template(self):
        suggestions = suggest_type('create database foo with template ',
                                   'create database foo with template ')

        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([{'type': 'database'}]))

    def test_drop_schema_qualified_table_suggests_only_tables(self):
        text = 'DROP TABLE schema_name.table_name'
        suggestions = suggest_type(text, text)
        self.assertEqual(suggestions, [{'type': 'table', 'schema': 'schema_name'}])

    @parameterized.expand([',', '  ,', 'sel ,'])
    def test_handle_pre_completion_comma_gracefully(self, text):
        suggestions = suggest_type(text, text)

        self.assertTrue(iter(suggestions))

    def test_cross_join(self):
        text = 'select * from v1 cross join v2 JOIN v1.id, '
        suggestions = suggest_type(text, text)
        self.assertEqual(self.sorted_dicts(suggestions), self.sorted_dicts([
            {'type': 'table', 'schema': []},
            {'type': 'view', 'schema': []},
            {'type': 'schema'}]))

    @parameterized.expand([
        'SELECT 1 AS ',
        'SELECT 1 FROM tabl AS ',
    ])
    def test_after_as(self, expression):
        suggestions = suggest_type(expression, expression)
        self.assertSetEqual(set(suggestions), set())

