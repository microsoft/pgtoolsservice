# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import mock

from pgsqltoolsservice.hosting import RequestContext


def get_mock_request_context() -> RequestContext:
    """
    Generates a request context with each send_* method replaced with a MagicMock
    :return: RequestContext with mocked send_* functions
    """
    mock_send_response = mock.MagicMock()
    mock_send_notification = mock.MagicMock()
    mock_send_error = mock.MagicMock()

    mock_request_context = RequestContext(None, None)
    mock_request_context.send_response = mock_send_response
    mock_request_context.send_notification = mock_send_notification
    mock_request_context.send_error = mock_send_error

    return mock_request_context
