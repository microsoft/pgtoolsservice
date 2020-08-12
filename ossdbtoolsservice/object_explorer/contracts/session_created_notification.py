# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional     # noqa

from ossdbtoolsservice.object_explorer.contracts.node_info import NodeInfo  # noqa


class SessionCreatedParameters:
    """Parameters to be sent back when an object explorer session is created"""

    def __init__(self):
        self.error_message: Optional[str] = None
        self.success: bool = True
        self.session_id: Optional[str] = None
        self.root_node: Optional[NodeInfo] = None


SESSION_CREATED_METHOD = 'objectexplorer/sessioncreated'
