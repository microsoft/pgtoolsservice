# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List     # noqa
import time
import unittest
from unittest.mock import Mock, patch

from ossdbtoolsservice.language.completion_refresher import CompletionRefresher
from ossdbtoolsservice.utils.constants import PG_PROVIDER_NAME, MYSQL_PROVIDER_NAME
from tests.mysqlsmo_tests.utils import MockMySQLServerConnection
import tests.pgsmo_tests.utils as utils

MYSCHEMA = 'myschema'
MYSCHEMA2 = 'myschema2'


class TestSqlCompletionRefresher(unittest.TestCase):
    """Methods for testing the SqlCompletion refresher module"""

    def setUp(self):
        self.refresher: CompletionRefresher = CompletionRefresher(utils.MockPGServerConnection())

    def test_ctor(self):
        """
        Refresher object should contain a few handlers
        """
        self.assertGreater(len(self.refresher.refreshers), 0)
        actual_handlers = list(self.refresher.refreshers.keys())
        expected_handlers = ['schemata', 'tables', 'views',
                             'types', 'databases', 'casing', 'functions']
        self.assertListEqual(expected_handlers, actual_handlers)

    def test_refresh_called_once(self):
        callbacks = Mock()

        with patch.object(self.refresher, '_bg_refresh') as bg_refresh:
            actual = self.refresher.refresh(callbacks)
            self.refresher._completer_thread.join()
            self.assertEqual(actual, 'Auto-completion refresh started in the background.')
            bg_refresh.assert_called_with(callbacks, None, None)

    def test_refresh_called_twice(self):
        """
        If refresh is called a second time, it should be restarted
        """
        callbacks = Mock()

        def dummy_bg_refresh(*args):
            time.sleep(0.2)  # seconds

        self.refresher._bg_refresh = dummy_bg_refresh

        actual1 = self.refresher.refresh(callbacks)
        self.assertEqual(actual1, 'Auto-completion refresh started in the background.')

        actual2 = self.refresher.refresh(callbacks)
        self.refresher._completer_thread.join()
        self.assertEqual(actual2, 'Auto-completion refresh restarted.')

    def test_refresh_with_callbacks(self):
        """
        Callbacks must be called
        """
        callbacks = [Mock()]
        metadata_executor_class = Mock()
        metadata_executor = Mock()
        metadata_executor.extra_args = {}

        with patch('ossdbtoolsservice.language.metadata_executor.MetadataExecutor', metadata_executor_class):
            # Set refreshers to 0: we're not testing refresh logic here
            self.refresher.refreshers = {}
            self.refresher.refresh(callbacks)
            self.refresher._completer_thread.join()
            self.assertEqual(callbacks[0].call_count, 1)
            
    def test_refresh_selects_pg_completer(self):
        """
        The correct completer (pg vs mysql) should be selected.
        """
        callbacks = Mock()
        pg_completer = Mock()
        mysql_completer = Mock()

        mock_completer_map = {
            PG_PROVIDER_NAME: pg_completer,
            MYSQL_PROVIDER_NAME: mysql_completer
        }
        with patch('ossdbtoolsservice.language.completion_refresher.COMPLETER_MAP', mock_completer_map):
            # Set refreshers to 0: we're not testing refresh logic here
            self.refresher.refreshers = {}
            self.refresher.refresh(callbacks)

            # PGCompleter, not MySQLCompleter, should be called because 
            # self.refresher is using a MockPGServerConnection
            pg_completer.assert_called_once()
            mysql_completer.assert_not_called()

    def test_refresh_selects_mysql_completer(self):
        mysql_refresher: CompletionRefresher = CompletionRefresher(MockMySQLServerConnection())
        callbacks = Mock()
        pg_completer = Mock()
        mysql_completer = Mock()       
         
        mock_completer_map = {
            PG_PROVIDER_NAME: pg_completer,
            MYSQL_PROVIDER_NAME: mysql_completer
        }
        with patch('ossdbtoolsservice.language.completion_refresher.COMPLETER_MAP', mock_completer_map):
            # Set refreshers to 0: we're not testing refresh logic here
            mysql_refresher.refreshers = {}
            mysql_refresher.refresh(callbacks)

            # MySQLCompleter, not PGCompleter, should be called because 
            # mysql_refresher is using a MockMySQLServerConnection
            mysql_completer.assert_called_once()
            pg_completer.assert_not_called()