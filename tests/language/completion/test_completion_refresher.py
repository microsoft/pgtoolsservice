import time
import unittest
from mock import Mock, patch

from pgsqltoolsservice.language.completion_refresher import CompletionRefresher



class TestSqlCompletionRefresher(unittest.TestCase):
    """Methods for testing the SqlCompletion refresher module"""

    def setUp(self):
        self.server = Mock()
        self.refresher: CompletionRefresher = CompletionRefresher(self.server)

    def test_ctor(self):
        """
        Refresher object should contain a few handlers
        :param refresher:
        :return:
        """
        assert len(self.refresher.refreshers) > 0
        actual_handlers = list(self.refresher.refreshers.keys())
        expected_handlers = ['schemata', 'tables', 'views',
                            'types', 'databases', 'casing', 'functions']
        assert expected_handlers == actual_handlers


    def test_refresh_called_once(self):
        """

        :param refresher:
        :return:
        """
        callbacks = Mock()

        with patch.object(self.refresher, '_bg_refresh') as bg_refresh:
            actual = self.refresher.refresh(callbacks)
            time.sleep(1)  # Wait for the thread to work.
            assert len(actual) == 1
            assert len(actual[0]) == 4
            assert actual[0][3] == 'Auto-completion refresh started in the background.'
            bg_refresh.assert_called_with(callbacks, None,
                None)


    def test_refresh_called_twice(self):
        """
        If refresh is called a second time, it should be restarted
        :param refresher:
        :return:
        """
        callbacks = Mock()

        def dummy_bg_refresh(*args):
            time.sleep(3)  # seconds

        self.refresher._bg_refresh = dummy_bg_refresh

        actual1 = self.refresher.refresh(callbacks)
        time.sleep(1)  # Wait for the thread to work.
        assert len(actual1) == 1
        assert len(actual1[0]) == 4
        assert actual1[0][3] == 'Auto-completion refresh started in the background.'

        actual2 = self.refresher.refresh(callbacks)
        time.sleep(1)  # Wait for the thread to work.
        assert len(actual2) == 1
        assert len(actual2[0]) == 4
        assert actual2[0][3] == 'Auto-completion refresh restarted.'


    # def test_refresh_with_callbacks(self):
    #     """
    #     Callbacks must be called
    #     :param refresher:
    #     """
    #     callbacks = [Mock()]
    #     pgexecute_class = Mock()
    #     pgexecute = Mock()
    #     pgexecute.extra_args = {}
    #     special = Mock()

    #     with patch('pgcli.completion_refresher.PGExecute', pgexecute_class):
    #         # Set refreshers to 0: we're not testing refresh logic here
    #         self.refresher.refreshers = {}
    #         self.refresher.refresh(callbacks)
    #         time.sleep(1)  # Wait for the thread to work.
    #         assert (callbacks[0].call_count == 1)
