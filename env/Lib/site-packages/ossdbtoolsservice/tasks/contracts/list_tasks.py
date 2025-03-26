# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization.serializable import Serializable


class ListTasksParameters(Serializable):
    """Parameters for the tasks/listtasks request"""

    list_active_tasks_only: bool | None

    def __init__(self) -> None:
        self.list_active_tasks_only = None


LIST_TASKS_REQUEST = IncomingMessageConfiguration("tasks/listtasks", ListTasksParameters)
