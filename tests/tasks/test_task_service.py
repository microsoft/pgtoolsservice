# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test the task service"""

from typing import List
import unittest
from unittest import mock

from pgsqltoolsservice.tasks import Task, TaskStatus, TaskService
from pgsqltoolsservice.tasks.contracts import CANCEL_TASK_REQUEST, CancelTaskParameters, LIST_TASKS_REQUEST, ListTasksParameters, TaskInfo
from pgsqltoolsservice.utils import constants
from tests.mock_request_validation import RequestFlowValidator
from tests.mocks.service_provider_mock import ServiceProviderMock


class TaskServiceTests(unittest.TestCase):
    """Methods for testing the task service"""
    def setUp(self):
        self.task_service = TaskService()
        self.service_provider = ServiceProviderMock({constants.TASK_SERVICE_NAME: self.task_service})
        self.request_validator = RequestFlowValidator()
        self.mock_task_1 = Task(None, None, None, None, None, self.request_validator.request_context, mock.Mock(), mock.Mock())
        self.request_validator.add_expected_notification(TaskInfo, 'tasks/newtaskcreated')
        self.mock_task_1.start = mock.Mock()
        self.mock_task_2 = Task(None, None, None, None, None, self.request_validator.request_context, mock.Mock(), mock.Mock())
        self.request_validator.add_expected_notification(TaskInfo, 'tasks/newtaskcreated')
        self.mock_task_2.start = mock.Mock()

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
        self.task_service.start_task(self.mock_task_1)
        self.task_service.start_task(self.mock_task_2)

        # Then the task service is aware of them
        self.assertIs(self.task_service._task_map[self.mock_task_1.id], self.mock_task_1)
        self.assertIs(self.task_service._task_map[self.mock_task_2.id], self.mock_task_2)

        # And the tasks' start methods were called
        self.mock_task_1.start.assert_called_once()
        self.mock_task_2.start.assert_called_once()

    def test_cancel_request(self):
        """Test that sending a cancellation request attempts to cancel the task"""
        # Set up a task
        self.mock_task_1.cancel = mock.Mock(return_value=True)
        self.mock_task_1.status = TaskStatus.IN_PROGRESS
        self.task_service.start_task(self.mock_task_1)

        # Set up the request flow validator
        self.request_validator.add_expected_response(bool, self.assertTrue)

        # If I call the cancellation handler
        params = CancelTaskParameters()
        params.task_id = self.mock_task_1.id
        self.task_service.handle_cancel_request(self.request_validator.request_context, params)

        # Then the task's cancel method should have been called and a positive response should have been sent
        self.mock_task_1.cancel.assert_called_once()
        self.request_validator.validate()

    def test_cancel_request_no_task(self):
        """Test that the cancellation handler returns false when there is no task to cancel"""
        # Set up the request flow validator
        self.request_validator.add_expected_response(bool, self.assertFalse)

        # If I call the cancellation handler without a corresponding task
        params = CancelTaskParameters()
        params.task_id = self.mock_task_1.id
        self.task_service.handle_cancel_request(self.request_validator.request_context, params)

        # Then a negative response should have been sent
        self.request_validator.validate()

    def test_list_all_tasks(self):
        """Test that the list task handler displays the correct task information"""
        self._test_list_tasks(False)

    def test_list_active_tasks(self):
        """Test that the list task handler displays the correct task information"""
        self._test_list_tasks(True)

    def _test_list_tasks(self, active_tasks_only: bool):
        # Set up task 1 to be in progress and task 2 to be complete
        self.task_service.start_task(self.mock_task_1)
        self.task_service.start_task(self.mock_task_2)
        self.mock_task_1.status = TaskStatus.IN_PROGRESS
        self.mock_task_2.status = TaskStatus.SUCCEEDED

        # Set up the request validator
        def validate_list_response(response_params: List[TaskInfo]):
            actual_response_dict = [info.__dict__ for info in response_params]
            expected_response_dict = [self.mock_task_1.task_info.__dict__]
            if not active_tasks_only:
                expected_response_dict.append(self.mock_task_2.task_info.__dict__)
            self.assertEqual(len(actual_response_dict), len(expected_response_dict))
            for expected_info in expected_response_dict:
                self.assertIn(expected_info, actual_response_dict)
        self.request_validator.add_expected_response(list, validate_list_response)

        # If I start the tasks and then list them
        self.task_service.start_task(self.mock_task_1)
        self.task_service.start_task(self.mock_task_2)
        params = ListTasksParameters()
        params.list_active_tasks_only = active_tasks_only
        self.task_service.handle_list_request(self.request_validator.request_context, params)

        # Then the service responds with TaskInfo for only task 1
        self.request_validator.validate()
