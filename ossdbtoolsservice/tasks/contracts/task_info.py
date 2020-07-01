# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.utils import constants


class TaskInfo:
    """Contract class for representing tasks"""

    def __init__(self, task_id: str, status: 'ossdbtoolsservice.tasks.TaskStatus', provider_name: str, server_name: str, database_name: str, task_name: str, description: str):
        self.task_id: str = task_id
        self.status: 'ossdbtoolsservice.tasks.TaskStatus' = status
        self.server_name: str = server_name
        self.database_name: str = database_name
        self.name: str = task_name
        self.description: str = description
        self.provider_name: str = provider_name
