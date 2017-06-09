# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import mock

from pgsqltoolsservice.hosting import RequestContext


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
