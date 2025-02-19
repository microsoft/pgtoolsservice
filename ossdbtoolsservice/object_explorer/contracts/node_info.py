# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.metadata.contracts import ObjectMetadata  # noqa
from ossdbtoolsservice.hosting import OutgoingMessageRegistration


class NodeInfo:
    """Contract for information on the connected PostgreSQL server"""

    node_path: str
    node_type: str
    label: str
    node_sub_type: str | None
    node_status: str | None
    is_leaf: bool
    metadata: ObjectMetadata
    error_message: str | None
    is_system: bool

    def __init__(
        self,
        label: str,
        node_path: str,
        node_type: str,
        metadata: ObjectMetadata | None,
        is_leaf: bool = False,
    ) -> None:
        self.node_path = node_path
        self.node_type = node_type
        self.label = label
        self.node_sub_type = None
        self.node_status = None
        self.is_leaf = is_leaf
        self.metadata = metadata or ObjectMetadata()
        self.error_message = None
        self.is_system = False


OutgoingMessageRegistration.register_outgoing_message(NodeInfo)
