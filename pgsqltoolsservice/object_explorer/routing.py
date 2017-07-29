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
        node.node_path = urljoin(current_path, self.path + '/')
        node.node_type = 'Folder'
        return node


class RoutingTarget:
    TNodeGenerator = TypeVar(Optional[Callable[[str, ObjectExplorerSession, dict], List[NodeInfo]]])

    def __init__(self, folders: Optional[List[Folder]], node_generator: TNodeGenerator):
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
        folder_nodes = [folder.as_node(current_path) for folder in self.folders]

        # Execute the node generator to generate the non-static nodes and add them after the folders
        if self.node_generator is not None:
            nodes = self.node_generator(current_path, session, match_params)
            folder_nodes.extend(nodes)

        return folder_nodes


# NODE GENERATORS ##########################################################


def _functions(current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    node_list: List[NodeInfo] = []
    schema = session.server.databases[session.server.maintenance_db].schemas[int(match_params['scid'])]
    for func in schema.functions:
        metadata = ObjectMetadata
        metadata.metadata_type = 0
        metadata.metadata_type_name = 'Function'
        metadata.name = func.name
        metadata.schema = schema.name

        node = NodeInfo()
        node.label = func.name
        node.isLeaf = True
        node.node_path = urljoin(current_path, str(func.oid))
        node.node_type = 'ScalarValuedFunction'
        node.metadata = metadata
        node_list.append(node)
    return node_list


def _tables(current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    node_list: List[NodeInfo] = []
    schema = session.server.databases[session.server.maintenance_db].schemas[int(match_params['scid'])]
    for table in schema.tables:
        metadata = ObjectMetadata()
        metadata.metadata_type = 0
        metadata.metadata_type_name = 'Table'
        metadata.name = table.name
        metadata.schema = schema.name

        cur_node = NodeInfo()
        cur_node.label = table.name
        cur_node.isLeaf = True
        cur_node.node_path = urljoin(current_path, str(table.oid))
        cur_node.node_type = 'Table'
        cur_node.metadata = metadata
        node_list.append(cur_node)
    return node_list


def _schemas(current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    node_list: List[NodeInfo] = []
    database = session.server.databases[session.server.maintenance_db]
    for schema in database.schemas:
        metadata = ObjectMetadata()
        metadata.metadata_type = 0
        metadata.metadata_type_name = 'Schema'
        metadata.schema = schema.name

        node = NodeInfo()
        node.label = schema.name
        node.isLeaf = False
        node.node_path = urljoin(current_path, str(schema.oid) + '/')
        node.node_type = 'Schema'
        node.metadata = metadata
        node_list.append(node)
    return node_list


def _views(current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    node_list: List[NodeInfo] = []
    schema = session.server.databases[session.server.maintenance_db].schemas[int(match_params['scid'])]
    for view in schema.views:
        metadata = ObjectMetadata()
        metadata.metadata_type = 0
        metadata.metadata_type_name = 'View'
        metadata.name = view.name
        metadata.schema = schema.name

        cur_node = NodeInfo()
        cur_node.label = view.name
        cur_node.isLeaf = True
        cur_node.node_path = urljoin(current_path, str(view.oid))
        cur_node.node_type = 'View'
        cur_node.metadata = metadata
        node_list.append(cur_node)
    return node_list


# ROUTING TABLE ############################################################


ROUTING_TABLE = {
    re.compile('^/$'): RoutingTarget(
        [Folder('Schemas', 'schemas'), Folder('Roles', 'roles'), Folder('Tablesapces', 'tablespaces')],
        None
    ),
    re.compile('^/schemas/$'): RoutingTarget(None, _schemas),
    re.compile('^/schemas/(?P<scid>\d+)/$'): RoutingTarget(
        [Folder('Tables', 'tables'), Folder('Views', 'views'), Folder('Functions', 'functions')],
        None
    ),
    re.compile('^/schemas/(?P<scid>\d+)/functions/$'): RoutingTarget(None, _functions),
    re.compile('^/schemas/(?P<scid>\d+)/tables/$'): RoutingTarget(None, _tables),
    re.compile('^/schemas/(?P<scid>\d+)/views/$'): RoutingTarget(None, _views)
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
