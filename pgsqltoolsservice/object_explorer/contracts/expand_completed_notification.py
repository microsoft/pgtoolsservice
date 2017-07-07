# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List # noqa
from pgsqltoolsservice.object_explorer.contracts.node_info import NodeInfo # noqa


class ExpandCompletedParameters:
    """Parameters to be sent back with a expand completed"""

    def __init__(self):
        self.error_message: str = None
        self.session_id: str = None
        self.nodes: List[NodeInfo] = None
        self.node_path: str = None


EXPAND_COMPLETED_METHOD = 'objectexplorer/expandCompleted'
