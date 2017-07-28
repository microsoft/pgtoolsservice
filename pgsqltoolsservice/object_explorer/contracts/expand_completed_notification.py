# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional  # noqa

from pgsqltoolsservice.object_explorer.contracts.node_info import NodeInfo  # noqa


class ExpandCompletedParameters:
    """Parameters to be sent back with a expand completed"""

    def __init__(self, session_id: str, node_path: str):
        self.error_message: Optional[str] = None
        self.session_id: str = session_id
        self.nodes: Optional[List[NodeInfo]] = None
        self.node_path: str = node_path


EXPAND_COMPLETED_METHOD = 'objectexplorer/expandCompleted'
