# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List
from pgsqltoolsservice.object_explorer.contracts.node_info import NodeInfo


class ExpandCompletedParameters:
    """Parameters to be sent back with a expand completed"""

    def __init__(self):
        self.error_message: str = None
        self.session_id: str = None
        self.nodes: List[NodeInfo] = List[NodeInfo]()
        self.node_path: str = None


EXPAND_COMPLETED_METHOD = 'objectexplorer/expandCompleted'
