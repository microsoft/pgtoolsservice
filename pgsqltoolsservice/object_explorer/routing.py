# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from typing import Callable, List, Optional, TypeVar
from urllib.parse import urljoin, urlparse

from pgsmo import NodeObject, Schema
from pgsqltoolsservice.metadata.contracts import ObjectMetadata
from pgsqltoolsservice.object_explorer.session import ObjectExplorerSession
from pgsqltoolsservice.object_explorer.contracts import NodeInfo


class Folder:
    """Defines a folder that should be added to the top of a list of nodes"""

    def __init__(self, label: str, path: str):
        """
        Initializes a folder
        :param label: Display name of the folder (will be returned to the user as-is)
        :param path: URI component to add to the end of the current path. A trailing slash will be added
                     Eg: If the path for the folder is oe://user@host:db/path/to/folder/ this
                     param should be 'folder'
        """
        self.label = label
        self.path = path + '/'

    def as_node(self, current_path: str) -> NodeInfo:
        """
        Generates a NodeInfo object that will represent the folder.
        :param current_path: The requested URI to expand/refresh
        :return: A non-leaf, folder node with the label and path from the object definition
        """
        node: NodeInfo = NodeInfo()
        node.is_leaf = False
        node.label = self.label
        node.node_path = urljoin(current_path, self.path)
        node.node_type = 'Folder'
        return node


class RoutingTarget:
    """
    Represents the target of a route. Can contain a list of folders, a function that generates a
    list of nodes or both.
    """
    # Type alias for an optional callable that takes in a current path, session, and parameters
    # from the regular expression match and returns a list of NodeInfo objects.
    TNodeGenerator = TypeVar(Optional[Callable[[str, ObjectExplorerSession, dict], List[NodeInfo]]])

    def __init__(self, folders: Optional[List[Folder]], node_generator: TNodeGenerator):
        """
        Initializes a routing target
        :param folders: A list of folders to return at the top of the expanded node results
        :param node_generator: A function that generates a list of nodes to show in the expanded results
        """
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
def _get_node_info(node: NodeObject, current_path: str, node_type: str, label: Optional[str]=None, is_leaf: bool=True) -> NodeInfo:
    """
    Utility method for generating a NodeInfo from a NodeObject
    :param node: NodeObject to convert into a NodeInfo.
                 node.name will be used for the label of the node (unless label is provided)
                 node.oid will be appended to the end of the current URI to create the node's path
    :param current_path: URI provided in the request to expand/refresh
    :param node_type: Node type, determines icon used in UI
    :param label: Overrides the node.name is provided, display name of the node displayed as-is
    :param is_leaf: Whether or not the node is a leaf. Default is true. If false, a trailing slash
                    will be added to the node path to indicate it behaves as a folder
    :return: NodeInfo based on the NodeObject provided
    """
    metadata = ObjectMetadata()
    metadata.metadata_type = 0
    metadata.metadata_type_name = type

    node_info: NodeInfo = NodeInfo()
    node_info.is_leaf = is_leaf
    node_info.label = label if label is not None else node.name
    node_info.metadata = metadata
    node_info.node_type = node_type

    trailing_slash = '' if is_leaf else '/'
    node_info.node_path = urljoin(current_path, str(node.oid) + trailing_slash)

    return node_info


def _get_schema(session: ObjectExplorerSession, scid: any) -> Schema:
    """Utility method to get a schema from the currently connect database"""
    return session.server.databases[session.server.maintenance_db].schemas[int(scid)]


def _functions(current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for functions in a schema
    Expected match_params:
    * scid int: schema OID
    """
    funcs = _get_schema(session, match_params['scid']).functions
    return [_get_node_info(node, current_path, 'ScalarValuedFunction') for node in funcs]


def _tables(current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for tables in a schema
    Expected match_params:
    * scid int: schema OID
    """
    tables = _get_schema(session, match_params['scid']).tables
    return [_get_node_info(node, current_path, 'Table') for node in tables]


def _schemas(current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """Function to generate a list of NodeInfo for tables in a schema"""
    schemas = session.server.databases[session.server.maintenance_db].schemas
    return [_get_node_info(node, current_path, 'Schema', is_leaf=False) for node in schemas]


def _views(current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for views in a schema
    Expected match_params:
    * scid int: schema OID
    """
    views = _get_schema(session, match_params['scid']).views
    return [_get_node_info(node, current_path, 'View') for node in views]


# ROUTING TABLE ############################################################
# This is the table that maps a regular expression to a routing target. When using route_request,
# the regular expression will be matched with the provided path. The routing target will then be
# used to generate a list of nodes that belong under the node. This can be a list of folders,
# a list of nodes generated by a function, or both.
# REGEX NOTES: (?P<name>...) is a named capture group
# (see https://docs.python.org/2/library/re.html#regular-expression-syntax)

ROUTING_TABLE = {
    re.compile('^/$'): RoutingTarget(
        [Folder('Schemas', 'schemas'), Folder('Roles', 'roles'), Folder('Tablespaces', 'tablespaces')],
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
    raise ValueError(f'Path {path} does not have a matching OE route')  # TODO: Localize
