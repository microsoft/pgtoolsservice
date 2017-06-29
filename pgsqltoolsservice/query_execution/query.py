# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from typing import List
from enum import Enum

from pgsqltoolsservice.query_execution.batch import Batch


class ExecutionState(Enum):
    NOT_STARTED = 'Not Started',
    EXECUTING = 'Executing',
    EXECUTED = 'Executed'


class Query:

    def __init__(self, batches: List[Batch] = None):
        self.batches = [] if batches is None else batches
        self.execution_state: ExecutionState = ExecutionState.NOT_STARTED
        self.is_canceled = False
