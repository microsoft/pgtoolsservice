# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import ossdbtoolsservice.utils as utils
from ossdbtoolsservice.hosting import IncomingMessageConfiguration


class ListTasksParameters:
    """Parameters for the tasks/listtasks request"""

    list_active_tasks_only: bool

    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self):
        self.list_active_tasks_only: bool = None


LIST_TASKS_REQUEST = IncomingMessageConfiguration("tasks/listtasks", ListTasksParameters)
