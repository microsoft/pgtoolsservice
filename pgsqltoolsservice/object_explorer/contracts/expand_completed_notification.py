# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List
from pgsqltoolsservice.connection.contracts.common import ConnectionSummary, ConnectionType     # noqa

class ExpandCompletedNotificationParams:
    """Parameters to be sent back with a connection complete event"""

    def __init__(self):
        self.error_message: str = None
        self.session_id: str = None
        self.nodes: List[NodeInfo] = None
        self.node_path: str = None

class NodeInfo(object):
    """Contract for information on the connected PostgreSQL server"""

    def __init__(self):
        self.node_path: str = None
        self.node_type: str = None
        self.label: str = None
        self.node_sub_type: str = None
        self.node_status: str = None
        self.is_leaf: bool = true
        self.metadata: ObjectMetadata = None
        self.error_message: str = None

class ObjectMetadata(object):
    """Contract for information on the connected PostgreSQL server"""

    def __init__(self):
        self.metadata_type: int = 0
        self.metadata_type_name: str = None
        self.schema: str = None
        self.name: str = None

EXPAND_COMPLETED_METHOD = 'objectexplorer/expandCompleted'
