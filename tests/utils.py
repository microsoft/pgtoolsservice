# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import unittest
import unittest.mock as mock
from typing import Optional

import psycopg2
import pymysql

from ossdbtoolsservice.hosting import (NotificationContext, RequestContext,
                                       ServiceProvider)
from ossdbtoolsservice.utils.constants import PG_PROVIDER_NAME
from pgsmo import Server
from smo.common.node_object import NodeCollection, NodeObject


def assert_not_none_or_empty(value: str):
    """Assertion to confirm a string to be not none or empty"""
    testcase = unittest.TestCase('__init__')
    testcase.assertIsNotNone(value)
    testcase.assertTrue(len(value))


def assert_not_none_or_whitespace(value: str):
    """Assertion to confirm a string is not none or whitespace"""
    testcase = unittest.TestCase('__init__')
    testcase.assertIsNotNone(value)
    testcase.assertTrue(len(value.strip()))


def get_mock_notification_context() -> NotificationContext:
    """
    Generates a notification context with the send_notification method mocked
    :return: NotificationContext with mocked send_notification
    """
    mock_send_notification = mock.MagicMock()

    mock_notification_context = NotificationContext(None)
    mock_notification_context.send_notification = mock_send_notification

    return mock_notification_context


def get_mock_logger() -> logging.Logger:
    """
    Generates a logger with mocked up log writing methods
    :return: Logger with mocked up log writing methods
    """
    mock_logger = logging.getLogger('mockLogger')
    mock_logger.exception = mock.MagicMock()
    mock_logger.critical = mock.MagicMock()
    mock_logger.debug = mock.MagicMock()
    mock_logger.error = mock.MagicMock()
    mock_logger.fatal = mock.MagicMock()
    mock_logger.warn = mock.MagicMock()
    mock_logger.warning = mock.MagicMock()
    mock_logger.info = mock.MagicMock()
    mock_logger.log = mock.MagicMock()

    return mock_logger


# PLEASE USE SERVICEPROVIDERMOCK from tests/mocks/service_provider_mock. #
# This mock will be deprecated #
def get_mock_service_provider(service_map: dict = None, provider_name: Optional[str] = PG_PROVIDER_NAME) -> ServiceProvider:
    """
    Generates a ServiceProvider with the given services

    :param service_map: A dictionary mapping service names to services
    """
    provider = ServiceProvider(None, {}, provider_name, get_mock_logger())
    if service_map is not None:
        provider._services = service_map
    provider._is_initialized = True
    return provider


class MockRequestContext(RequestContext):
    """Mock RequestContext object that allows service responses, notifications, and errors to be tested"""

    def __init__(self):
        RequestContext.__init__(self, None, None)
        self.last_response_params = None
        self.last_notification_method = None
        self.last_notification_params = None
        self.last_error_message = None
        self.send_response = mock.Mock(side_effect=self.send_response_impl)
        self.send_notification = mock.Mock(side_effect=self.send_notification_impl)
        self.send_error = mock.Mock(side_effect=self.send_error_impl)
        self.send_unhandled_error_response = mock.Mock(side_effect=self.send_unhandled_error_response_impl)

    def send_response_impl(self, params):
        self.last_response_params = params

    def send_notification_impl(self, method, params):
        self.last_notification_method = method
        self.last_notification_params = params

    def send_error_impl(self, message, data=None, code=0):
        self.last_error_message = message

    def send_unhandled_error_response_impl(self, ex: Exception):
        self.last_error_message = str(ex)


class MockPyMySQLCursor:
    """Class used to mock pymysql cursor objects for testing"""

    def __init__(self, query_results, columns_names=[], connection=mock.Mock()):
        self.execute = mock.Mock(side_effect=self.execute_success_side_effects)
        self.fetchall = mock.Mock(return_value=query_results)
        self.fetchone = mock.Mock(side_effect=self.execute_fetch_one_side_effects)
        self.close = mock.Mock()
        self.connection = connection
        self.rowcount = -1
        self._mogrified_value = b'Some query'
        self.mogrify = mock.Mock(return_value=self._mogrified_value)
        self._query_results = query_results
        self._fetched_count = 0

    def __iter__(self):
        return self

    def __next__(self):
        next_row = self.execute_fetch_one_side_effects()

        if next_row is None:
            raise StopIteration

        return next_row

    def execute_success_side_effects(self, *args):
        """Set up dummy results for query execution success"""
        self.rowcount = len(self._query_results) if self._query_results is not None else 0

    def execute_failure_side_effects(self, *args):
        """Set up dummy results and raise error for query execution failure"""
        self.connection.notices = ["NOTICE: foo", "DEBUG: bar"]
        raise pymysql.DatabaseError()

    def execute_fetch_one_side_effects(self, *args):
        if self._fetched_count < len(self._query_results):
            row = self._query_results[self._fetched_count]
            self._fetched_count += 1
            return row

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    @property
    def mogrified_value(self):
        return self._mogrified_value


class MockPyMySQLConnection(object):
    """Class used to mock pymysql connection objects for testing"""

    def __init__(self, parameters=None, cursor=None):
        self.close = mock.Mock()
        self.cursor = mock.Mock(return_value=cursor)
        self.commit = mock.Mock()
        self.ping = mock.Mock()


class MockThread():
    """Mock thread class that mocks the thread's start method to run target code without actually starting a thread"""

    def __init__(self):
        self.target = None
        self.args = None
        self.start = None

    def initialize_target(self, target, args):
        self.target = target
        self.args = args
        self.start = mock.Mock(side_effect=lambda: self.target(*self.args))
        return self


# OBJECT TEST HELPERS ######################################################

def assert_node_collection(prop: any, attrib: any):
    test_case = unittest.TestCase('__init__')
    test_case.assertIsInstance(attrib, NodeCollection)
    test_case.assertIs(prop, attrib)


def assert_threeway_equals(target: any, attrib: any, prop: any):
    test_case = unittest.TestCase('__init__')
    test_case.assertEqual(attrib, target)
    test_case.assertEqual(prop, target)


def assert_is_not_none_or_whitespace(target: str):
    test_case = unittest.TestCase('__init__')
    test_case.assertIsNotNone(target)
    test_case.assertIsInstance(target, str)
    test_case.assertNotEqual(target.strip(), '')


# MOCK NODE OBJECT #########################################################
class MockNodeObject(NodeObject):
    @classmethod
    def _from_node_query(cls, root_server: Server, parent: Optional[NodeObject], **kwargs):
        pass

    def __init__(self, root_server: Server, parent: Optional[NodeObject], name: str):
        super(MockNodeObject, self).__init__(root_server, parent, name)

    @classmethod
    def _template_root(cls, root_server: Server):
        return 'template_root'

    @property
    def template_vars(self) -> str:
        pass

    def get_database_node(self):
        return mock.MagicMock(datlastsysoid=None)
