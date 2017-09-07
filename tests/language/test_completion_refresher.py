# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Any
import time
import unittest
from mock import Mock, patch

from pgsmo import NodeCollection, Server
from pgsqltoolsservice.language.completion_refresher import CompletionRefresher

import tests.pgsmo_tests.utils as utils

MYSCHEMA = 'myschema'
MYSCHEMA2 = 'myschema2'


class TestSqlCompletionRefresher(unittest.TestCase):
    """Methods for testing the SqlCompletion refresher module"""

    def setUp(self):
        mock_server = Server(utils.MockConnection(None))
        self.refresher: CompletionRefresher = CompletionRefresher(mock_server)

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

        with patch('pgsqltoolsservice.language.metadata_executor.MetadataExecutor', metadata_executor_class):
            # Set refreshers to 0: we're not testing refresh logic here
            self.refresher.refreshers = {}
            self.refresher.refresh(callbacks)
            self.refresher._completer_thread.join()
            self.assertEqual(callbacks[0].call_count, 1)

    # Helper functions ##################################################################
    def _as_node_collection(self, object_list: List[Any]) -> NodeCollection[Any]:
        return NodeCollection(lambda: object_list)
