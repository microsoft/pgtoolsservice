# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.metadata.contracts import ObjectMetadata


class NodeInfo(object):
    """Contract for information on the connected PostgreSQL server"""

    def __init__(self):
        self.node_path: str = None
        self.node_type: str = None
        self.label: str = None
        self.node_sub_type: str = None
        self.node_status: str = None
        self.is_leaf: bool = True
        self.metadata: ObjectMetadata = ObjectMetadata()
        self.error_message: str = None
