# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import enum
from ossdbtoolsservice.hosting import OutgoingMessageRegistration

class TaskStatus(enum.Enum):
    """Enum representing task status"""
    NOT_STARTED = 0
    IN_PROGRESS = 1
    SUCCEEDED = 2
    SUCCEEDED_WITH_WARNING = 3
    FAILED = 4
    CANCELED = 5

class TaskInfo:
    """Contract class for representing tasks"""
    task_id: str
    status: TaskStatus
    server_name: str
    database_name: str
    name: str
    description: str
    provider_name: str

    def __init__(
            self,
            task_id: str,
            status: TaskStatus,
            provider_name: str,
            server_name: str,
            database_name: str,
            task_name: str,
            description: str):
        self.task_id: str = task_id
        self.status: TaskStatus = status
        self.server_name: str = server_name
        self.database_name: str = database_name
        self.name: str = task_name
        self.description: str = description
        self.provider_name: str = provider_name

OutgoingMessageRegistration.register_outgoing_message(TaskInfo)