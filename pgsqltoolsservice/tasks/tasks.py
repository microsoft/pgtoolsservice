# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing the task service, allowing long-running asynchronous operations"""

import enum
import threading
import time
from typing import Callable, Dict  # noqa
import uuid

from pgsqltoolsservice.hosting import RequestContext
from pgsqltoolsservice.tasks.contracts import TaskInfo


class TaskStatus(enum.Enum):
    """Enum representing task status"""
    NOT_STARTED = 0
    IN_PROGRESS = 1
    SUCCEEDED = 2
    SUCCEEDED_WITH_WARNING = 3
    FAILED = 4
    CANCELED = 5


class TaskResult:
    """Class representing the result of a task execution"""

    def __init__(self, status: TaskStatus, error_message: str = None):
        self.status = status
        self.error_message = error_message


class Task:
    """Class representing a single task handled by the task service"""

    def __init__(self, name: str, description: str, provider_name: str, server_name: str, database_name: str, request_context: RequestContext, action,
                 on_cancel: Callable = None) -> None:
        self.name = name
        self.description = description
        self.provider_name = provider_name
        self.server_name = server_name
        self.database_name = database_name
        self.id: str = str(uuid.uuid4())
        self.status: TaskStatus = TaskStatus.NOT_STARTED
        self.status_message: str = None
        self.on_cancel: Callable = on_cancel
        self.cancellation_lock: threading.Lock = threading.Lock()
        self.canceled: bool = False
        self._request_context = request_context
        self._start_time: float = None
        self._action = action
        self._thread: threading.Thread = None
        self._notify_created()

    @property
    def task_info(self) -> TaskInfo:
        """Create a TaskInfo object corresponding to this task"""
        return TaskInfo(self.id, self.status, self.server_name, self.database_name, self.name, self.description)

    def start(self) -> None:
        """Start the task by running it in a new thread"""
        self._start_time = time.clock()
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._thread.start()

    def cancel(self) -> bool:
        """Cancel the task if it is running and return true, or return false if the task is not running"""
        if self.status is not TaskStatus.IN_PROGRESS:
            return False
        with self.cancellation_lock:
            if self.on_cancel:
                try:
                    self.on_cancel()
                except Exception:
                    return False
            self.canceled = True
        return True

    def _run(self) -> None:
        """Run the given action, updating the task's status as needed"""
        self._set_status(TaskStatus.IN_PROGRESS)
        try:
            task_result: TaskResult = self._action(self)
            if self.canceled:
                self._set_status(TaskStatus.CANCELED)
            else:
                self._set_status(task_result.status, task_result.error_message)
        except Exception as e:
            self._set_status(TaskStatus.FAILED, str(e))

    def _set_status(self, new_status: TaskStatus, new_message: str = None) -> None:
        self.status = new_status
        self.status_message = new_message
        self._notify_status_changed()

    def _notify_created(self) -> None:
        if self.status is not TaskStatus.NOT_STARTED:
            return
        self._request_context.send_notification('tasks/newtaskcreated', self.task_info)

    def _notify_status_changed(self) -> None:
        self._request_context.send_notification('tasks/statuschanged', {
            'taskId': self.id,
            'status': self.status,
            'message': self.status_message or '',
            'duration': int((time.clock() - self._start_time) * 1000) if self._is_completed else 0
        })

    def _is_completed(self) -> bool:
        return self.status in [TaskStatus.CANCELED, TaskStatus.FAILED, TaskStatus.SUCCEEDED, TaskStatus.SUCCEEDED_WITH_WARNING]
