# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import logging
import re
import unittest
import unittest.mock as mock
from typing import Any, Callable, Optional

import psycopg
from psycopg.connection import AdaptersMap

from ossdbtoolsservice.hosting import (
    NotificationContext,
    RequestContext,
    ServiceProvider,
)
from ossdbtoolsservice.hosting.json_message import JSONRPCMessage
from ossdbtoolsservice.hosting.message_server import MessageServer

NoticeHandler = Callable[[str], None]


def assert_not_none_or_empty(value: str):
    """Assertion to confirm a string to be not none or empty"""
    testcase = unittest.TestCase("__init__")
    testcase.assertIsNotNone(value)
    testcase.assertTrue(len(value))


def assert_not_none_or_whitespace(value: str):
    """Assertion to confirm a string is not none or whitespace"""
    testcase = unittest.TestCase("__init__")
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
    mock_logger = logging.getLogger("mockLogger")
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
def get_mock_service_provider(
    service_map: dict | None = None,
) -> ServiceProvider:
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
    """Mock RequestContext object that allows service responses, notifications,
    and errors to be tested"""

    def __init__(self, raise_on_error: bool = False) -> None:
        RequestContext.__init__(self, None, None)
        self.raise_on_error = raise_on_error
        self.last_response_params = None
        self.last_notification_method = None
        self.last_notification_params = None
        self.last_error_message = None
        self.send_response = mock.Mock(side_effect=self.send_response_impl)
        self.send_notification = mock.Mock(side_effect=self.send_notification_impl)
        self.send_error = mock.Mock(side_effect=self.send_error_impl)
        self.send_unhandled_error_response = mock.Mock(
            side_effect=self.send_unhandled_error_response_impl
        )

    def send_response_impl(self, params) -> None:
        self.last_response_params = params

    def send_notification_impl(self, method, params):
        self.last_notification_method = method
        self.last_notification_params = params

    def send_error_impl(self, message, data=None, code=0) -> None:
        if self.raise_on_error:
            raise Exception(message)
        self.last_error_message = message

    def send_unhandled_error_response_impl(self, ex: Exception):
        self.last_error_message = str(ex)


class MockPsycopgConnection:
    """Class used to mock psycopg connection objects for testing"""

    TransactionStatus = mock.Mock(return_value=psycopg.pq.TransactionStatus.IDLE)

    def __init__(self, dsn_parameters=None, cursor=None):
        self.close = mock.Mock()
        self.dsn_parameters = dsn_parameters
        self.server_version = "131001"
        self.cursor = mock.MagicMock(return_value=cursor)
        self.autocommit = True
        self.commit = mock.Mock()
        self.pgconn = mock.Mock()
        self.info = MockConnectionInfo(dsn_parameters, self.server_version)
        self.broken = False

        self._adapters: Optional[AdaptersMap] = mock.Mock()
        self.notice_handlers: list[NoticeHandler] = []

    @property
    def closed(self):
        """Mock for the connection's closed property"""
        return self.close.call_count > 0

    @property
    def adapters(self) -> AdaptersMap:
        return self._adapters

    def get_dsn_parameters(self):
        """Mock for the connection's get_dsn_parameters method"""
        return self.dsn_parameters

    def get_parameter_status(self, parameter):
        """Mock for the connection's get_parameter_status method"""
        if parameter == "server_version":
            return self.server_version
        else:
            raise NotImplementedError()

    def add_notice_handler(self, callback: NoticeHandler) -> None:
        """
        Register a callable to be invoked when a notice message is received.

        :param callback: the callback to call upon message received.
        :type callback: Callable[[~psycopg.errors.Diagnostic], None]
        """
        self.notice_handlers.append(callback)


class MockConnectionInfo:
    def __init__(self, dsn_parameters, server_version) -> None:
        self.dsn = dsn_parameters
        self.server_version = server_version
        self.backend_pid = mock.Mock(return_value=0)
        self.transaction_status = psycopg.pq.TransactionStatus.IDLE

    def get_parameters(self):
        # split by spaces unless in quotes or double quotes
        parts = re.split(
            r'\s(?=(?:(?:[^"\'\\]*(?:\\.|"(?:[^"\\]*\\.)*[^"\\]*"|\'(?:[^\'\\]*\\.)*[^\'\\]*\')*))[^"\'\\]*$)',
            self.dsn,
        )
        dsn_parameters = {}
        for part in parts:
            key, value = part.split("=")
            # Remove quotes or double quotes if they exist
            value = re.sub(r'^[\'"]|[\'"]$', "", value)
            dsn_parameters[key] = value
        return dsn_parameters


class MockCursor:
    """Class used to mock psycopg cursor objects for testing"""

    def __init__(self, query_results, columns_names=None, connection=None):
        if connection is None:
            connection = mock.Mock()
        if columns_names is None:
            columns_names = []
        self.execute = mock.Mock(side_effect=self.execute_success_side_effects)
        self.fetchall = mock.Mock(return_value=query_results)
        self.fetchone = mock.Mock(side_effect=self.execute_fetch_one_side_effects)
        self.close = mock.Mock()
        self.connection = connection.connection
        self.description = [
            self.create_column_description(name=name) for name in columns_names
        ]
        self.rowcount = -1
        self._mogrified_value = "Some query"
        self.mogrify = mock.Mock(return_value=self._mogrified_value)
        self._query_results = query_results
        self._fetched_count = 0
        self.statusmessage = None

    def __iter__(self):
        return self

    def __next__(self):
        next_row = self.execute_fetch_one_side_effects()

        if next_row is None:
            raise StopIteration

        return next_row

    def execute_success_side_effects(self, *args, **kwargs) -> None:
        """Set up dummy results for query execution success"""
        for handler in self.connection.notice_handlers:
            handler(MockNotice("foo", "NOTICE"))
            handler(MockNotice("bar", "DEBUG"))
        self.rowcount = len(self._query_results) if self._query_results is not None else 0

    def execute_failure_side_effects(self, *args):
        """Set up dummy results and raise error for query execution failure"""
        for handler in self.connection.notice_handlers:
            handler(MockNotice("foo", "NOTICE"))
            handler(MockNotice("bar", "DEBUG"))
        raise psycopg.DatabaseError()

    def execute_fetch_one_side_effects(self, *args):
        if self._fetched_count < len(self._query_results):
            row = self._query_results[self._fetched_count]
            self._fetched_count += 1
            return row

    def create_column_description(self, **kwargs):
        description = {
            "name": None,
            "type_code": None,
            "display_size": None,
            "internal_size": None,
            "precision": None,
            "scale": None,
            "null_ok": None,
        }
        merge = {**description, **dict(kwargs)}
        tup = tuple(merge.values())
        column = mock.Mock()

        def _side_effect(index: int) -> Any:
            return tup[index]

        column.__getitem__ = mock.Mock(side_effect=_side_effect)
        column.type_display = "text"
        return column

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    @property
    def mogrified_value(self) -> str:
        return self._mogrified_value


class MockThread:
    """Mock thread class that mocks the thread's start method to run target
    code without actually starting a thread"""

    def __init__(self):
        self.target = None
        self.args = None
        self.start = None

    def initialize_target(self, target, args):
        self.target = target
        self.args = args
        self.start = mock.Mock(side_effect=lambda: self.target(*self.args))
        return self


class MockNotice:
    def __init__(self, message_primary, severity):
        self.message_primary = message_primary
        self.severity = severity


class MockMessageServer(MessageServer):
    def __init__(self):
        super().__init__(async_runner=None, logger=get_mock_logger())
        self.sent_messages = []

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def _send_message(self, message: JSONRPCMessage) -> None:
        self.sent_messages.append(message)

    def recieve_message(self, message: JSONRPCMessage) -> None:
        self._dispatch_message(message)


def get_fully_qualified_type_name(obj: type) -> str:
    return f"{obj.__module__}.{obj.__qualname__}"
