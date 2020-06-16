# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional  # noqa

from ostoolsservice.object_explorer.contracts.node_info import NodeInfo  # noqa


class ExpandCompletedParameters:
    """Parameters to be sent back with a expand completed"""

    def __init__(self, session_id: str, node_path: str):
        """
        Initialize parameters to return when an expand operation is completed
        :param session_id: ID for the session that had an expanded
        :param node_path: Path to the node that was expanded
        """
        self.session_id: str = session_id
        self.node_path: str = node_path

        self.error_message: Optional[str] = None
        self.nodes: Optional[List[NodeInfo]] = None


EXPAND_COMPLETED_METHOD = 'objectexplorer/expandCompleted'
