# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import unittest
import unittest.mock as mock
import psycopg2

from pgsqltoolsservice.hosting import NotificationContext, RequestContext, ServiceProvider


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
def get_mock_service_provider(service_map: dict = None) -> ServiceProvider:
    """
    Generates a ServiceProvider with the given services

    :param service_map: A dictionary mapping service names to services
    """
    provider = ServiceProvider(None, {}, get_mock_logger())
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


class MockConnection(object):
    """Class used to mock psycopg2 connection objects for testing"""

    def __init__(self, dsn_parameters=None, cursor=None):
        self.close = mock.Mock()
        self.dsn_parameters = dsn_parameters
        self.server_version = '90602'
        self.cursor = mock.Mock(return_value=cursor)
        self.get_backend_pid = mock.Mock(return_value=0)
        self.notices = []
        self.get_transaction_status = mock.Mock(return_value=psycopg2.extensions.TRANSACTION_STATUS_IDLE)

    @property
    def closed(self):
        """Mock for the connection's closed property"""
        return self.close.call_count > 0

    def get_dsn_parameters(self):
        """Mock for the connection's get_dsn_parameters method"""
        return self.dsn_parameters

    def get_parameter_status(self, parameter):
        """Mock for the connection's get_parameter_status method"""
        if parameter == 'server_version':
            return self.server_version
        else:
            raise NotImplementedError()


class MockCursor:
    """Class used to mock psycopg2 cursor objects for testing"""

    def __init__(self, query_results):
        self.execute = mock.Mock(side_effect=self.execute_success_side_effects)
        self.fetchall = mock.Mock(return_value=query_results)
        self.close = mock.Mock()
        self.connection = mock.Mock()
        self.description = None
        self.rowcount = -1

    def execute_success_side_effects(self, *args):
        """Set up dummy results for query execution success"""
        self.connection.notices = ["NOTICE: foo", "DEBUG: bar"]
        self.description = []

    def execute_failure_side_effects(self, *args):
        """Set up dummy results and raise error for query execution failure"""
        self.connection.notices = ["NOTICE: foo", "DEBUG: bar"]
        raise psycopg2.DatabaseError()
