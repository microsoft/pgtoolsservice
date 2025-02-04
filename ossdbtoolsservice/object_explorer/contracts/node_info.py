# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.metadata.contracts import ObjectMetadata  # noqa
from ossdbtoolsservice.hosting import OutgoingMessageRegistration


class NodeInfo(object):
    """Contract for information on the connected PostgreSQL server"""
    node_path: str
    node_type: str
    label: str
    node_sub_type: str
    node_status: str
    is_leaf: bool
    metadata: ObjectMetadata
    error_message: str
    is_system: bool

    def __init__(self):
        self.node_path: str = None
        self.node_type: str = None
        self.label: str = None
        self.node_sub_type: str = None
        self.node_status: str = None
        self.is_leaf: bool = True
        self.metadata: ObjectMetadata = ObjectMetadata()
        self.error_message: str = None
        self.is_system: bool = False


OutgoingMessageRegistration.register_outgoing_message(NodeInfo)
