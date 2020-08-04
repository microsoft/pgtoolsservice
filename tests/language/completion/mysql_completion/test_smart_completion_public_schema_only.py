import unittest
from unittest.mock import Mock

import pytest
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document

from ossdbtoolsservice.language.completion.mysql_completer import MySQLCompleter

metadata = {
    'users': ['id', 'email', 'first_name', 'last_name'],
    'orders': ['id', 'ordered_date', 'status'],
    'select': ['id', 'insert', 'ABC'],
    'réveillé': ['id', 'insert', 'ABC']
}


class TestSmartCompletion(unittest.TestCase):

    def setUp(self):
        self.completer = MySQLCompleter(smart_completion=True)

        tables, columns = [], []

        for table, cols in metadata.items():
            tables.append((table,))
            columns.extend([(table, col) for col in cols])

        self.completer.set_dbname('test')
        self.completer.extend_schemata('test')
        self.completer.extend_relations(tables, kind='tables')
        self.completer.extend_columns(columns, kind='tables')
        self.keywords = self.completer.keywords_tree.keys()
        self.complete_event = Mock()


    def test_empty_string_completion(self):
        text = ''
        position = 0
        result = set(
            self.completer.get_completions(
                Document(text=text, cursor_position=position),
                self.complete_event))
        self.assertSetEqual(result, set(map(lambda completion: Completion(completion, display_meta='keyword'), sorted(self.keywords))))


    def test_select_keyword_completion(self):
        text = 'SEL'
        position = len('SEL')
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set([Completion(text='SELECT', start_position=-3, display_meta='keyword')]))


    def test_table_completion(self):
        text = 'SELECT * FROM '
        position = len(text)
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position), self.complete_event))
        self.assertSetEqual(result,  set([
            Completion(text='`réveillé`', start_position=0, display_meta='table'),
            Completion(text='`select`', start_position=0, display_meta='table'),
            Completion(text='orders', start_position=0, display_meta='table'),
            Completion(text='users', start_position=0, display_meta='table'),
        ]))


    def test_function_name_completion(self):
        text = 'SELECT MA'
        position = len('SELECT MA')
        result = self.completer.get_completions(
            Document(text=text, cursor_position=position), self.complete_event)
        print(result)
        # Set comparison: > means "is superset"
        self.assertTrue(set(result) > set([Completion(text='MAX', start_position=-2, display_meta='function'),
                                Completion(text='MASTER', start_position=-2, display_meta='keyword'),
                                ]))


    def test_suggested_column_names(self):
        """Suggest column and function names when selecting from table.

        :param completer:
        :param complete_event:
        :return:

        """
        text = 'SELECT  from users'
        position = len('SELECT ')
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set([
            Completion(text='*', start_position=0, display_meta='column'),
            Completion(text='email', start_position=0, display_meta='column'),
            Completion(text='first_name', start_position=0, display_meta='column'),
            Completion(text='id', start_position=0, display_meta='column'),
            Completion(text='last_name', start_position=0, display_meta='column'),
        ] +
            list(map(lambda completion: Completion(completion, display_meta='function'), self.completer.functions)) +
            [Completion(text='users', start_position=0,  display_meta='alias')] +
            list(map(lambda completion: Completion(completion, display_meta='keyword'), self.keywords))))


    def test_suggested_column_names_in_function(self):
        """Suggest column and function names when selecting multiple columns from
        table.

        :param completer:
        :param complete_event:
        :return:

        """
        text = 'SELECT MAX( from users'
        position = len('SELECT MAX(')
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set([
            Completion(text='*', start_position=0, display_meta='column'),
            Completion(text='email', start_position=0, display_meta='column'),
            Completion(text='first_name', start_position=0, display_meta='column'),
            Completion(text='id', start_position=0, display_meta='column'),
            Completion(text='last_name', start_position=0, display_meta='column')]))


    def test_suggested_column_names_with_table_dot(self):
        """Suggest column names on table name and dot.

        :param completer:
        :param complete_event:
        :return:

        """
        text = 'SELECT users. from users'
        position = len('SELECT users.')
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set([
            Completion(text='*', start_position=0, display_meta='column'),
            Completion(text='email', start_position=0, display_meta='column'),
            Completion(text='first_name', start_position=0, display_meta='column'),
            Completion(text='id', start_position=0, display_meta='column'),
            Completion(text='last_name', start_position=0, display_meta='column')]))


    def test_suggested_column_names_with_alias(self):
        """Suggest column names on table alias and dot.

        :param completer:
        :param complete_event:
        :return:

        """
        text = 'SELECT u. from users u'
        position = len('SELECT u.')
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set([
            Completion(text='*', start_position=0, display_meta='column'),
            Completion(text='email', start_position=0, display_meta='column'),
            Completion(text='first_name', start_position=0, display_meta='column'),
            Completion(text='id', start_position=0, display_meta='column'),
            Completion(text='last_name', start_position=0, display_meta='column')]))


    def test_suggested_multiple_column_names(self):
        """Suggest column and function names when selecting multiple columns from
        table.

        :param completer:
        :param complete_event:
        :return:

        """
        text = 'SELECT id,  from users u'
        position = len('SELECT id, ')
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set([
            Completion(text='*', start_position=0, display_meta='column'),
            Completion(text='email', start_position=0, display_meta='column'),
            Completion(text='first_name', start_position=0, display_meta='column'),
            Completion(text='id', start_position=0, display_meta='column'),
            Completion(text='last_name', start_position=0, display_meta='column')] +
            list(map(lambda completion: Completion(completion, display_meta='function'), self.completer.functions)) +
            [Completion(text='u', start_position=0, display_meta='alias')] +
            list(map(lambda completion: Completion(completion, display_meta='keyword'), self.keywords))))


    def test_suggested_multiple_column_names_with_alias(self):
        """Suggest column names on table alias and dot when selecting multiple
        columns from table.

        :param completer:
        :param complete_event:
        :return:

        """
        text = 'SELECT u.id, u. from users u'
        position = len('SELECT u.id, u.')
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set([
            Completion(text='*', start_position=0, display_meta='column'),
            Completion(text='email', start_position=0, display_meta='column'),
            Completion(text='first_name', start_position=0, display_meta='column'),
            Completion(text='id', start_position=0, display_meta='column'),
            Completion(text='last_name', start_position=0, display_meta='column')]))


    def test_suggested_multiple_column_names_with_dot(self):
        """Suggest column names on table names and dot when selecting multiple
        columns from table.

        :param completer:
        :param complete_event:
        :return:

        """
        text = 'SELECT users.id, users. from users u'
        position = len('SELECT users.id, users.')
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set([
            Completion(text='*', start_position=0, display_meta='column'),
            Completion(text='email', start_position=0, display_meta='column'),
            Completion(text='first_name', start_position=0, display_meta='column'),
            Completion(text='id', start_position=0, display_meta='column'),
            Completion(text='last_name', start_position=0, display_meta='column')]))


    def test_suggested_aliases_after_on(self):
        text = 'SELECT u.name, o.id FROM users u JOIN orders o ON '
        position = len('SELECT u.name, o.id FROM users u JOIN orders o ON ')
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set([
            Completion(text='o', start_position=0, display_meta='alias'),
            Completion(text='u', start_position=0, display_meta='alias')]))


    def test_suggested_aliases_after_on_right_side(self):
        text = 'SELECT u.name, o.id FROM users u JOIN orders o ON o.user_id = '
        position = len(
            'SELECT u.name, o.id FROM users u JOIN orders o ON o.user_id = ')
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set([
            Completion(text='o', start_position=0, display_meta='alias'),
            Completion(text='u', start_position=0, display_meta='alias')]))


    def test_suggested_tables_after_on(self):
        text = 'SELECT users.name, orders.id FROM users JOIN orders ON '
        position = len('SELECT users.name, orders.id FROM users JOIN orders ON ')
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set([
            Completion(text='orders', start_position=0, display_meta='alias'),
            Completion(text='users', start_position=0, display_meta='alias')]))


    def test_suggested_tables_after_on_right_side(self):
        text = 'SELECT users.name, orders.id FROM users JOIN orders ON orders.user_id = '
        position = len(
            'SELECT users.name, orders.id FROM users JOIN orders ON orders.user_id = ')
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set([
            Completion(text='orders', start_position=0, display_meta='alias'),
            Completion(text='users', start_position=0, display_meta='alias')]))


    def test_table_names_after_from(self):
        text = 'SELECT * FROM '
        position = len('SELECT * FROM ')
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set([
            Completion(text='`réveillé`', start_position=0, display_meta='table'),
            Completion(text='`select`', start_position=0, display_meta='table'),
            Completion(text='orders', start_position=0, display_meta='table'),
            Completion(text='users', start_position=0, display_meta='table'),
        ]))


    def test_auto_escaped_col_names(self):
        text = 'SELECT  from `select`'
        position = len('SELECT ')
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set([
            Completion(text='*', start_position=0, display_meta='column'),
            Completion(text='`ABC`', start_position=0, display_meta='column'),
            Completion(text='`insert`', start_position=0, display_meta='column'),
            Completion(text='id', start_position=0, display_meta='column'),
        ] + \
            list(map(lambda completion: Completion(completion, display_meta='function'), self.completer.functions)) + \
            [Completion(text='`select`', start_position=0, display_meta='alias')] + \
            list(map(lambda completion: Completion(completion, display_meta='keyword'), self.keywords))))


    def test_un_escaped_table_names(self):
        text = 'SELECT  from réveillé'
        position = len('SELECT ')
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))
        self.assertSetEqual(result, set([
            Completion(text='*', start_position=0, display_meta='column'),
            Completion(text='`ABC`', start_position=0, display_meta='column'),
            Completion(text='`insert`', start_position=0, display_meta='column'),
            Completion(text='id', start_position=0, display_meta='column'),
        ] +
            list(map(lambda completion: Completion(completion, display_meta='function'), self.completer.functions)) +
            [Completion(text='réveillé', start_position=0, display_meta='alias')] +
            list(map(lambda completion: Completion(completion, display_meta='keyword'), self.keywords))))

    def test_keyword_lower_casing(self):
        self.completer.keyword_casing = 'lower'

        text = 'SEL'
        position = len(text)
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))

        # then completions should now be lower case
        self.assertSetEqual(result, set([Completion(text='select', start_position=-3, display_meta="keyword")]))

    def test_keyword_upper_casing(self):
        self.completer.keyword_casing = 'upper'

        text = 'sel'
        position = len(text)
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))

        # then completions should now be lower case
        self.assertSetEqual(result, set([Completion(text='SELECT', start_position=-3, display_meta="keyword")]))

    def test_keyword_auto_casing(self):
        self.completer.keyword_casing = 'auto'
        
        # if text is lower case   
        text = 'sel'
        position = len(text)
        result = set(self.completer.get_completions(
            Document(text=text, cursor_position=position),
            self.complete_event))

        # then completions should be lower case as well
        self.assertSetEqual(result, set([Completion(text='select', start_position=-3, display_meta="keyword")]))