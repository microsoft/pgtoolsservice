# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils


class CancelTaskParameters:
    """Parameters for the tasks/canceltask request"""

    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self):
        self.task_id: str = None


CANCEL_TASK_REQUEST = IncomingMessageConfiguration('tasks/canceltask', CancelTaskParameters)
