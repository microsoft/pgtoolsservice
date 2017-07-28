# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from typing import Callable, List, Optional, TypeVar
from urllib.parse import urljoin, urlparse

from pgsqltoolsservice.metadata.contracts import ObjectMetadata
from pgsqltoolsservice.object_explorer.session import ObjectExplorerSession
from pgsqltoolsservice.object_explorer.contracts import NodeInfo


class Folder:
    def __init__(self, label: str, path: str):
        self.label = label
        self.path = path

    def as_node(self, current_path: str) -> NodeInfo:
        node = NodeInfo()
        node.is_leaf = False
        node.label = self.label
        node.node_path = urljoin(current_path, self.path)
        node.node_type = 'Folder'
        return node


class RoutingTarget:
    TNodeGenerator = TypeVar(Optional[Callable[[str, ObjectExplorerSession, dict], List[NodeInfo]]])

    def __init__(self, folders: Optional(List[Folder]), node_generator: TNodeGenerator):
        self.folders: List[Folder] = folders or []
        self.node_generator = node_generator

    def get_nodes(self, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
        """
        Builds a list of NodeInfo that should be displayed under the current routing path
        :param current_path: The requested node path
        :param session: OE Session that the lookup will be performed from
        :param match_params: The captures from the regex that this routing target is mapped from
        :return: A list of NodeInfo
        """
        # Start by adding the static folders
        folder_nodes = [folder.as_node for folder in self.folders]

        # Execute the node generator to generate the non-static nodes and add them after the folders
        if self.node_generator is not None:
            nodes = self.node_generator(current_path, session, match_params)
            folder_nodes.extend(nodes)

        return folder_nodes


# NODE GENERATORS ##########################################################


def _functions(current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    node_list: List[NodeInfo] = []
    database = session.server.databases[session.server.maintenance_db]
    for schema in database.schemas:
        for function in schema.functions:
            metadata = ObjectMetadata
            metadata.metadata_type = 0
            metadata.metadata_type_name = 'Function'
            metadata.name = function.name
            metadata.schema = schema.name

            node = NodeInfo()
            node.label = function.name
            node.isLeaf = True
            node.node_path = urljoin(current_path, function.oid)
            node.node_type = 'ScalarValuedFunction'
            node.metadata = metadata
            node_list.append(node)
    return node_list


def _tables(current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    node_list: List[NodeInfo] = []
    database = session.server.databases[session.server.maintenance_db]
    for schema in database.schemas:
        for table in schema.tables:
            metadata = ObjectMetadata()
            metadata.metadata_type = 0
            metadata.metadata_type_name = 'Table'
            metadata.name = table.name
            metadata.schema = schema.name

            cur_node = NodeInfo()
            cur_node.label = f'{schema.name}.{table.name}'
            cur_node.isLeaf = True
            cur_node.node_path = urljoin(current_path, table.oid)
            cur_node.node_type = 'Table'
            cur_node.metadata = metadata
            node_list.append(cur_node)
    return node_list


def _views(current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    node_list: List[NodeInfo] = []
    database = session.server.databases[session.server.maintenance_db]
    for schema in database.schemas:
        for view in schema.views:
            metadata = ObjectMetadata()
            metadata.metadata_type = 0
            metadata.metadata_type_name = 'View'
            metadata.name = view.name
            metadata.schema = schema.name

            cur_node = NodeInfo()
            cur_node.label = f'{schema.name}.{view.name}'
            cur_node.isLeaf = True
            cur_node.node_path = urljoin(current_path, view.oid)
            cur_node.node_type = 'View'
            cur_node.metadata = metadata
            node_list.append(cur_node)
    return node_list


# ROUTING TABLE ############################################################


ROUTING_TABLE = {
    re.compile('^/$'): RoutingTarget(
        [Folder('Tables', 'tables'), Folder('Views', 'views'), Folder('Functions', 'functions')],
        None
    ),
    re.compile('^/functions/$'): RoutingTarget(None, _functions),
    re.compile('^/tables/$'): RoutingTarget(None, _tables),
    re.compile('^/views/$'): RoutingTarget(None, _views)
}


# PUBLIC FUNCTIONS #########################################################


def route_request(session: ObjectExplorerSession, path: str) -> List[NodeInfo]:
    """
    Performs a lookup for a given expand request
    :param session: Session that the expand is being performed on
    :param path: Path of the object to expand
    :return: List of nodes that result from the expansion
    """
    # Figure out what the path we're looking at is
    path = urlparse(path).path

    # Find a matching route for the path
    for route, target in ROUTING_TABLE.items():
        match = route.match(path)
        if match is not None:
            # We have a match!
            return target.get_nodes(path, session, match.groupdict())

    # If we make it to here, there isn't a route that matches the path
    raise RuntimeError(f'Path {path} does not have a matching OE route')  # TODO: Localize
