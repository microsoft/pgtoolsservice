# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds the task service, which supports management and tracking of active tasks"""

from typing import Dict  # noqa

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider  # noqa
from pgsqltoolsservice.tasks import Task, TaskStatus  # noqa
from pgsqltoolsservice.tasks.contracts import CANCEL_TASK_REQUEST, CancelTaskParameters, LIST_TASKS_REQUEST, ListTasksParameters  # noqa


class TaskService:
    """Manage long-running tasks"""

    def __init__(self):
        self._task_map: Dict[str, Task] = {}
        self._service_provider = None

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider

        # Register the handlers for the service
        self._service_provider.server.set_request_handler(CANCEL_TASK_REQUEST, self.handle_cancel_request)
        self._service_provider.server.set_request_handler(LIST_TASKS_REQUEST, self.handle_list_request)

    def handle_cancel_request(self, request_context: RequestContext, params: CancelTaskParameters) -> None:
        """Respond to tasks/canceltask requests by canceling the requested task"""
        try:
            request_context.send_response(self._task_map[params.task_id].cancel())
        except KeyError:
            request_context.send_response(False)

    def handle_list_request(self, request_context: RequestContext, params: ListTasksParameters) -> None:
        """Respond to tasks/listtasks requests by returning the TaskInfo for all tasks"""
        tasks = list(self._task_map.values())
        if params.list_active_tasks_only:
            tasks = [task for task in tasks if task.status is TaskStatus.IN_PROGRESS]
        request_context.send_response([task.task_info for task in tasks])

    def start_task(self, task: Task) -> None:
        """Register a task so that it can be listed and canceled, then start it"""
        self._task_map[task.id] = task
        task.start()
