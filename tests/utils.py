# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import unittest.mock as mock

from pgsqltoolsservice.hosting import NotificationContext, RequestContext


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
    mock_logger.info = mock.MagicMock()
    mock_logger.log = mock.MagicMock()

    return mock_logger


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

    def send_response_impl(self, params):
        self.last_response_params = params

    def send_notification_impl(self, method, params):
        self.last_notification_method = method
        self.last_notification_params = params

    def send_error_impl(self, message, data=None, code=0):
        self.last_error_message = message
