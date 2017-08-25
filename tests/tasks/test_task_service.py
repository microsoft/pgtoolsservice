# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test the task service"""

import unittest
from unittest import mock

from pgsqltoolsservice.tasks import Task, TaskService
from pgsqltoolsservice.tasks.contracts import CANCEL_TASK_REQUEST, LIST_TASKS_REQUEST
from pgsqltoolsservice.utils import constants
from tests.mocks.service_provider_mock import ServiceProviderMock
from tests.utils import MockRequestContext


class TaskServiceTests(unittest.TestCase):
    """Methods for testing the task service"""
    def setUp(self):
        self.task_service = TaskService()
        self.service_provider = ServiceProviderMock({constants.TASK_SERVICE_NAME: self.task_service})
        self.request_context = MockRequestContext()
        self.mock_test_1 = Task(None, None, None, None, None, self.request_context, mock.Mock(), mock.Mock())
        self.mock_test_1.start = mock.Mock()
        self.mock_test_2 = Task(None, None, None, None, None, self.request_context, mock.Mock(), mock.Mock())
        self.mock_test_2.start = mock.Mock()

    def test_registration(self):
        """Test that the service registers its cancel and list methods correctly"""
        # If I call the task service's register method
        self.task_service.register(self.service_provider)

        # Then CANCEL_TASK_REQUEST and LIST_TASKS_REQUEST should have been registered
        self.service_provider.server.set_request_handler.assert_has_calls(
            [mock.call(CANCEL_TASK_REQUEST, self.task_service.handle_cancel_request), mock.call(LIST_TASKS_REQUEST, self.task_service.handle_list_request)],
            any_order=True)        

    def test_start_task(self):
        """Test that the service can start tasks"""
        # If I start both tasks
        self.task_service.start_task(self.mock_test_1)
        self.task_service.start_task(self.mock_test_2)

        # Then the task service is aware of them
        self.assertIs(self.task_service._task_map[self.mock_test_1.id], self.mock_test_1)
        self.assertIs(self.task_service._task_map[self.mock_test_2.id], self.mock_test_2)

        # And the tasks' start methods were called
        self.mock_test_1.start.assert_called_once()
        self.mock_test_2.start.assert_called_once()

    def test_cancel_request(self):
        """Test that sending a cancellation request attempts to cancel the task"""
        # Set up a task
        pass

    def test_cancel_request_no_task(self):
        """Test that the cancellation handler returns false when there is no task to cancel"""
        pass

    def test_list_tasks(self):
        """Test that the list task handler displays the correct task information"""
        pass
