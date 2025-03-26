# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization.serializable import Serializable


class CancelTaskParameters(Serializable):
    """Parameters for the tasks/canceltask request"""

    task_id: str | None

    def __init__(self) -> None:
        self.task_id = None


CANCEL_TASK_REQUEST = IncomingMessageConfiguration("tasks/canceltask", CancelTaskParameters)
