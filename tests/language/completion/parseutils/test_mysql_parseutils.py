import unittest

from ossdbtoolsservice.language.completion.packages.parseutils.mysql_utils.mysql_utils import \
    extract_tables

class TestMySQLParseUtils(unittest.TestCase):

    def test_empty_string(self):
        tables = extract_tables('')
        self.assertEqual(tables, [])


    def test_simple_select_single_table(self):
        tables = extract_tables('select * from abc')
        self.assertEqual(tables, [(None, 'abc', None)])


    def test_simple_select_single_table_schema_qualified(self):
        tables = extract_tables('select * from abc.def')
        self.assertEqual(tables,[('abc', 'def', None)])


    def test_simple_select_multiple_tables(self):
        tables = extract_tables('select * from abc, def')
        self.assertEqual(sorted(tables), [(None, 'abc', None), (None, 'def', None)])


    def test_simple_select_multiple_tables_schema_qualified(self):
        tables = extract_tables('select * from abc.def, ghi.jkl')
        self.assertEqual(sorted(tables), [('abc', 'def', None), ('ghi', 'jkl', None)])


    def test_simple_select_with_cols_single_table(self):
        tables = extract_tables('select a,b from abc')
        self.assertEqual(tables, [(None, 'abc', None)])


    def test_simple_select_with_cols_single_table_schema_qualified(self):
        tables = extract_tables('select a,b from abc.def')
        self.assertEqual(tables, [('abc', 'def', None)])


    def test_simple_select_with_cols_multiple_tables(self):
        tables = extract_tables('select a,b from abc, def')
        self.assertEqual(sorted(tables), [(None, 'abc', None), (None, 'def', None)])


    def test_simple_select_with_cols_multiple_tables_with_schema(self):
        tables = extract_tables('select a,b from abc.def, def.ghi')
        self.assertEqual(sorted(tables), [('abc', 'def', None), ('def', 'ghi', None)])


    def test_select_with_hanging_comma_single_table(self):
        tables = extract_tables('select a, from abc')
        self.assertEqual(tables, [(None, 'abc', None)])


    def test_select_with_hanging_comma_multiple_tables(self):
        tables = extract_tables('select a, from abc, def')
        self.assertEqual(sorted(tables), [(None, 'abc', None), (None, 'def', None)])


    def test_select_with_hanging_period_multiple_tables(self):
        tables = extract_tables('SELECT t1. FROM tabl1 t1, tabl2 t2')
        self.assertEqual(sorted(tables), [(None, 'tabl1', 't1'), (None, 'tabl2', 't2')])


    def test_simple_insert_single_table(self):
        tables = extract_tables('insert into abc (id, name) values (1, "def")')

        # sqlparse mistakenly assigns an alias to the table
        # self.assertEqual(tables, [(None, 'abc', None)]
        self.assertEqual(tables, [(None, 'abc', 'abc')])


    def test_simple_insert_single_table_schema_qualified(self):
        tables = extract_tables('insert into abc.def (id, name) values (1, "def")')
        self.assertEqual(tables, [('abc', 'def', None)])


    def test_simple_update_table(self):
        tables = extract_tables('update abc set id = 1')
        self.assertEqual(tables, [(None, 'abc', None)])


    def test_simple_update_table_with_schema(self):
        tables = extract_tables('update abc.def set id = 1')
        self.assertEqual(tables, [('abc', 'def', None)])


    def test_join_table(self):
        tables = extract_tables('SELECT * FROM abc a JOIN def d ON a.id = d.num')
        self.assertEqual(sorted(tables), [(None, 'abc', 'a'), (None, 'def', 'd')])


    def test_join_table_schema_qualified(self):
        tables = extract_tables(
            'SELECT * FROM abc.def x JOIN ghi.jkl y ON x.id = y.num')
        self.assertEqual(tables, [('abc', 'def', 'x'), ('ghi', 'jkl', 'y')])


    def test_join_as_table(self):
        tables = extract_tables('SELECT * FROM my_table AS m WHERE m.a > 5')
        self.assertEqual(tables, [(None, 'my_table', 'm')])