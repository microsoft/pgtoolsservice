# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test the task logic"""

import unittest
from unittest import mock

from ossdbtoolsservice.tasks import Task, TaskResult, TaskStatus
from ossdbtoolsservice.utils import constants
from tests import utils


class TestTasks(unittest.TestCase):
    """Methods for testing the Task class"""

    def setUp(self):
        """Set up the data for tasks"""
        self.mock_action = mock.Mock(return_value=TaskResult(TaskStatus.SUCCEEDED))
        self.task_name = 'test_name'
        self.task_description = 'test_description'
        self.task_provider = constants.MYSQL_PROVIDER_NAME
        self.server_name = 'test_server'
        self.database_name = 'test_db'
        self.request_context = utils.MockRequestContext()

    def create_task(self) -> Task:
        """Create a task using the test's data"""
        return Task(self.task_name, self.task_description, self.task_provider, self.server_name, self.database_name, self.request_context, self.mock_action)

    def test_initialization(self):
        """Test that the task is initialized with the correct default values and sends a creation notification"""
        # If I initialize a task
        task = self.create_task()
        # Then the task's status gets set correctly
        self.assertIs(task.status, TaskStatus.NOT_STARTED)
        self.assertIsNone(task.status_message)
        # And the task sends a task/newtaskcreated notification
        self.assertEqual(self.request_context.last_notification_method, 'tasks/newtaskcreated')
        expected_params = {
            'status': TaskStatus.NOT_STARTED,
            'server_name': self.server_name,
            'database_name': self.database_name,
            'name': self.task_name,
            'provider_name': self.task_provider,
            'description': self.task_description
        }
        actual_params = self.request_context.last_notification_params.__dict__
        for param, value in expected_params.items():
            self.assertIn(param, actual_params)
            self.assertEqual(value, actual_params[param])
        self.assertIn('task_id', actual_params)

    def test_run_task(self):
        """Test that the task can be started, runs in a separate thread, and sends status notifications"""
        # If I kick off a task and wait for it to complete
        task = self.create_task()
        task.start()
        task._thread.join()
        # Then it should have executed the task's action
        self.mock_action.assert_called_once()
        # And it should have sent notifications when the task started and ended
        expected_method = 'tasks/statuschanged'
        notification_calls = self.request_context.send_notification.mock_calls
        self.assertEqual(len(notification_calls), 3)
        first_call_method = notification_calls[1][1][0]
        self.assertEqual(first_call_method, expected_method)
        first_call_params = notification_calls[1][1][1]
        expected_first_params = {
            'status': TaskStatus.IN_PROGRESS,
            'message': ''
        }
        for param, value in expected_first_params.items():
            self.assertIn(param, first_call_params)
            self.assertEqual(value, first_call_params[param])
        self.assertIn('duration', first_call_params)
        self.assertGreaterEqual(first_call_params['duration'], 0)
        self.assertIn('taskId', first_call_params)
        second_call_method = notification_calls[2][1][0]
        self.assertEqual(second_call_method, expected_method)
        second_call_params = notification_calls[2][1][1]
        expected_second_params = {
            'status': TaskStatus.SUCCEEDED,
            'message': ''
        }
        for param, value in expected_second_params.items():
            self.assertIn(param, second_call_params)
            self.assertEqual(value, second_call_params[param])
        self.assertIn('taskId', second_call_params)
        self.assertIn('duration', second_call_params)

    def test_task_fails(self):
        """Test that the task is handled correctly when execution fails"""
        # Set up the task's action to throw an error when executing
        exception_message = 'test_message'
        self.mock_action.side_effect = Exception(exception_message)
        # If I kick off a task whose execution raises an exception, and wait for it to execute
        task = self.create_task()
        task.start()
        task._thread.join()
        # Then the task's status is properly marked as failed and the status message shows the error
        self.assertIs(task.status, TaskStatus.FAILED)
        self.assertEqual(task.status_message, exception_message)

    def test_cancel(self):
        """Test that canceling a task calls its cancellation callback and sets the canceled flag"""
        # Set up the task with a cancellation callback
        task = self.create_task()
        task.on_cancel = mock.Mock()
        task.status = TaskStatus.IN_PROGRESS

        # If I cancel a task that is in progress
        cancel_result = task.cancel()

        # Then the cancellation handler was called and the task is marked as canceled
        self.assertTrue(cancel_result)
        task.on_cancel.assert_called_once()
        self.assertTrue(task.canceled)

    def test_cancel_not_in_progress(self):
        """Test that canceling a task that is not in progress does not succeed"""
        # Set up the task with a cancellation callback
        task = self.create_task()
        task.on_cancel = mock.Mock()
        task.status = TaskStatus.NOT_STARTED

        # If I cancel a task that is not in progress
        cancel_result = task.cancel()

        # Then the cancellation handler was not called and the task is not marked as canceled
        self.assertFalse(cancel_result)
        task.on_cancel.assert_not_called()
        self.assertFalse(task.canceled)

    def test_cancel_callback_fails(self):
        """Test that if the cancellation callback fails, the task is not marked as canceled"""
        # Set up the task with a cancellation callback that raises an exception when called
        task = self.create_task()
        task.on_cancel = mock.Mock(side_effect=Exception)
        task.status = TaskStatus.IN_PROGRESS

        # If I cancel a task and its cancellation callback raises an exception
        cancel_result = task.cancel()

        # Then the task is not marked as canceled and the call to cancel returned false
        self.assertFalse(cancel_result)
        self.assertFalse(task.canceled)
