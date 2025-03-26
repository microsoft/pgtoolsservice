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
    server_name: str | None
    database_name: str | None
    name: str
    description: str
    provider_name: str

    def __init__(
        self,
        task_id: str,
        status: TaskStatus,
        provider_name: str,
        server_name: str | None,
        database_name: str | None,
        task_name: str,
        description: str,
    ) -> None:
        self.task_id = task_id
        self.status = status
        self.server_name = server_name
        self.database_name = database_name
        self.name = task_name
        self.description = description
        self.provider_name = provider_name


OutgoingMessageRegistration.register_outgoing_message(TaskInfo)
