# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization.serializable import convert_from_dict


class CancelTaskParameters:
    """Parameters for the tasks/canceltask request"""
    task_id: str

    @classmethod
    def from_dict(cls, dictionary: dict):
        return convert_from_dict(cls, dictionary)

    def __init__(self):
        self.task_id: str = None


CANCEL_TASK_REQUEST = IncomingMessageConfiguration('tasks/canceltask', CancelTaskParameters)
