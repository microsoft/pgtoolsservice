# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List
from pgsqltoolsservice.object_explorer.contracts.node_info import NodeInfo

class SessionCreatedParameters:
    """Parameters to be sent back when an object explorer session is created"""

    def __init__(self):
        self.success: bool = True
        self.session_id: str = None
        self.root_node: NodeInfo = None

SESSION_CREATED_METHOD = 'objectexplorer/sessioncreated'
