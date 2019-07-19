# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from urllib.parse import urljoin, urlparse
from typing import Callable, Dict, List, Optional, TypeVar, Union

from smo.common.node_object import NodeObject
from mysqlsmo import *
from pgsqltoolsservice.metadata.contracts import ObjectMetadata
from pgsqltoolsservice.object_explorer.session import ObjectExplorerSession, Folder, RoutingTarget
from pgsqltoolsservice.object_explorer.contracts import NodeInfo

# NODE GENERATOR HELPERS ###################################################
def _get_node_info(
        node: NodeObject,
        current_path: str,
        node_type: str,
        label: Optional[str] = None,
        is_leaf: bool = True
) -> NodeInfo:
    """
    Utility method for generating a NodeInfo from a NodeObject
    :param node: NodeObject to convert into a NodeInfo.
                 node.name will be used for the label of the node (unless label is provided)
                 node.oid will be appended to the end of the current URI to create the node's path
    :param current_path: URI provided in the request to expand/refresh
    :param node_type: Node type, determines icon used in UI
    :param label: Overrides the node.name if provided, display name of the node displayed as-is
    :param is_leaf: Whether or not the node is a leaf. Default is true. If false, a trailing slash
                    will be added to the node path to indicate it behaves as a folder
    :return: NodeInfo based on the NodeObject provided
    """
    # Generate the object metadata
    metadata = ObjectMetadata(node.urn, None, type(node).__name__, node.name, None)
    # Add the schema name if it is the immediate parent
    if node.parent is not None and node.parent.parent is None and hasattr(node, 'schema'):
        metadata.schema = node.schema
    node_info: NodeInfo = NodeInfo()
    node_info.is_leaf = is_leaf
    node_info.label = label if label is not None else node.name
    node_info.metadata = metadata
    node_info.node_type = node_type

    # Build the path to the node. Trailing slash is added to indicate URI is a folder
    trailing_slash = '' if is_leaf else '/'
    node_info.node_path = urljoin(current_path, str(node.name) + trailing_slash)

    return node_info


TRefreshObject = TypeVar('NodeObject')


def _get_obj_with_refresh(parent_obj: TRefreshObject, is_refresh: bool) -> TRefreshObject:
    if is_refresh:
        parent_obj.refresh()
    return parent_obj


def _get_table_or_view(is_refresh: bool, session: ObjectExplorerSession, dbid: any, parent_type: str, tid: any) -> Union[Table, View]:
    tid = int(tid)
    if parent_type == 'tables':
        return _get_obj_with_refresh(session.server.databases[int(dbid)].tables[tid], is_refresh)
    elif parent_type == 'views':
        return _get_obj_with_refresh(session.server.databases[int(dbid)].views[tid], is_refresh)
    elif parent_type == 'materializedviews':
        return _get_obj_with_refresh(session.server.databases[int(dbid)].materialized_views[tid], is_refresh)
    else:
        raise ValueError('Object type to retrieve nodes is invalid')  # TODO: Localize


# NODE GENERATORS ##########################################################
def _columns(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate column NodeInfo for tables/views
      dbid int: Database OID
      obj str: Type of the object to get columns from
      tid int: table or view OID
    """
    nodes = Column.get_nodes_for_parent(root_server=None, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'events', label=f'{node.schema}.{node.name}')
        for node in nodes
    ]


def _constraints(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate constraint NodeInfo for tables
      dbid int: Database OID
      tid int: Table or View OID
    """
    table = _get_obj_with_refresh(session.server.databases[int(match_params['dbid'])].tables[int(match_params['tid'])], is_refresh)
    node_info = []
    node_info.extend([_get_node_info(node, current_path, 'Constraint') for node in table.check_constraints])
    node_info.extend([_get_node_info(node, current_path, 'Constraint') for node in table.exclusion_constraints])
    node_info.extend([_get_node_info(node, current_path, 'Key_ForeignKey') for node in table.foreign_key_constraints])
    node_info.extend([_get_node_info(node, current_path, 'Constraint') for node in table.index_constraints])

    return sorted(node_info, key=lambda x: x.label)


def _functions(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for functions in a schema
    Expected match_params:
      dbid int: Database OID
    """
    nodes = Function.get_nodes_for_parent(root_server=None, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'functions', label=f'{node.schema}.{node.name}')
        for node in nodes
    ]

def _procedures(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for functions in a schema
    Expected match_params:
      dbid int: Database OID
    """
    nodes = Procedure.get_nodes_for_parent(root_server=None, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'procedures', label=f'{node.schema}.{node.name}')
        for node in nodes
    ]

def _collations(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for collations in a schema
    Expected match_params:
      dbid int: Database OID
    """
    nodes = Collation.get_nodes_for_parent(root_server=None, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'collations', label=f'{node.schema}.{node.name}')
        for node in nodes
    ]

def _charsets(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for character set in a schema
    Expected match_params:
      dbid int: Database OID
    """
    nodes = CharacterSet.get_nodes_for_parent(root_server=None, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'charsets', label=f'{node.schema}.{node.name}')
        for node in nodes
    ]


def _indexes(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate index NodeInfo for tables
    Expected match_params:
      dbid int: Database OID
      tid int: table OID
    """
    nodes = Index.get_nodes_for_parent(root_server=None, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'indexes', label=f'{node.schema}.{node.name}')
        for node in nodes
    ]


def is_system_request(route_path: str):
    return '/system/' in route_path


def _tables(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for tables in a schema
    Expected match_params:
      dbid int: Database OID
    """
    root_server=session.server
    nodes = Table.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'Table', label=f'{node.name}')
        for node in nodes
    ]


def _users(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """Function to generate a list of users for a server"""
    root_server=session.server
    nodes = User.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'Role', label=f'{node.name}')
        for node in nodes
    ]

def _sysdatabases(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """Function to generate a list of databases"""
    root_server=session.server
    nodes = Database.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'Database', label=f'{node.name}', is_leaf=False)
        for node in nodes if node.name in ["information_schema", "mysql", "performance_schema"]
    ]

def _databases(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """Function to generate a list of databases"""
    root_server=session.server
    nodes = Database.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'Database', label=f'{node.name}', is_leaf=False)
        for node in nodes if node.name not in ["information_schema", "mysql", "performance_schema"]
    ]


def _tablespaces(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """Function to generate a list of tablespaces for a server"""
    root_server=session.server
    nodes = Tablespace.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'tablespaces', label=f'{node.schema}.{node.name}')
        for node in nodes
    ]


def _triggers(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """Function to generate a list of triggers for a table or view"""
    nodes = Trigger.get_nodes_for_parent(root_server=None, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'triggers', label=f'{node.schema}.{node.name}')
        for node in nodes
    ]


def _views(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for views in a schema
    Expected match_params:
      scid int: schema OID
    """
    nodes = View.get_nodes_for_parent(root_server=None, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'views', label=f'{node.schema}.{node.name}')
        for node in nodes
    ]

def _events(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict):
    nodes = Event.get_nodes_for_parent(root_server=None, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'events', label=f'{node.schema}.{node.name}')
        for node in nodes
    ]

def _default_node_generator(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> None:
    """
    Clears cached Object Explorer Node information so that the refreshed node and its children fetches the data again when expanded
    """
    if is_refresh:
        session.server.refresh()


# ROUTING TABLE ############################################################
# This is the table that maps a regular expression to a routing target. When using route_request,
# the regular expression will be matched with the provided path. The routing target will then be
# used to generate a list of nodes that belong under the node. This can be a list of folders,
# a list of nodes generated by a function, or both.
# REGEX NOTES: (?P<name>...) is a named capture group
# (see https://docs.python.org/2/library/re.html#regular-expression-syntax)

MYSQL_ROUTING_TABLE = {
    # Clicked on the server, Databases, Roles, Tablespaces folders pop up
    re.compile(r'^/$'): RoutingTarget(
        [
            Folder('Character Sets', 'charsets'),
            Folder('Databases', 'databases'),
            Folder('System Databases', 'systemdatabases'),
            Folder('Users', 'users'),
            Folder('Tablespaces', 'tablespaces')
        ],
        _default_node_generator
    ),
    # Clicked on Databases folder, should list databases underneath
    re.compile(r'^/(?P<db>databases)/$'): RoutingTarget(
        None, 
        _databases
    ),
    # Clicked on Sytem Databases folder, should list system databases underneath
    re.compile(r'^/(?P<db>systemdatabases)/$'): RoutingTarget(
        None,
        _sysdatabases
    ),
    # Clicked on one of the Databases or System Databases nodes, should list the folders within the database
    re.compile(r'^/(?P<db>databases|systemdatabases)/(?P<dbname>\w+)/$'): RoutingTarget(
        [
            Folder('Tables', 'tables'),
            Folder('Views', 'views'),
            Folder('Stored Procedures', 'procedures'),
            Folder('Functions', 'functions'),
            Folder('Events', 'events')
        ],
        _default_node_generator
    ),
    # Clicked on the Tables folder, should list table nodes
    re.compile(r'^/(?P<db>databases|systemdatabases)/(?P<dbname>\w+)/tables/$'): RoutingTarget(
        None, 
        _tables
    ),
    # Clicked on the Views folder, should list System View Folder and view nodes
    re.compile(r'^/(?P<db>databases|systemdatabases)/(?P<dbname>\w+)/views/$'): RoutingTarget(
       None,
        _views
    ),
    # Clicked on the Stored Procedures folder, should list procedure nodes
    re.compile(r'^/(?P<db>databases|systemdatabases)/(?P<dbname>\w+)/procedures/$'): RoutingTarget(
        None,
        _procedures
    ),
    # Clicked on the Functions folder, should list function nodes
    re.compile(r'^/(?P<db>databases|systemdatabases)/(?P<dbname>\w+)/functions/$'): RoutingTarget(
        None,
        _functions
    ),
    # Clicked on the Events folder
    re.compile(r'^/(?P<db>databases|systemdatabases)/(?P<dbname>\w+)/events/$'): RoutingTarget(
        None,
        _events
    ),
    # Clicked on one of the tables, should list folders within the table
    re.compile(r'^/(?P<db>databases|systemdatabases)/(?P<dbname>\w+)/tables/(?P<tbl_name>\w+)/$'): RoutingTarget(
        [
            Folder('Columns', 'columns'),
            Folder('Constraints', 'constraints'),
            Folder('Indexes', 'indexes'),
            Folder('Triggers', 'triggers')
        ],
        _default_node_generator
    ),
    # Clicked on one particular view node, should list folders within the view
    re.compile(r'^/(?P<db>databases|systemdatabases)/(?P<dbname>\w+)/views/(?P<tbl_name>\w+/$)'): RoutingTarget(
        [
            Folder('Columns', 'columns')
        ],
        _default_node_generator
    ),
    # Clicked on the Constraints folder inside one table
    re.compile(r'^/(?P<db>databases|systemdatabases)/(?P<dbname>\w+)/tables/(?P<tbl_name>\w+)/constraints/$'): RoutingTarget(
        None, 
        _constraints
    ),
    # Clicked on the Indexes folder inside one table
    re.compile(r'^/(?P<db>databases|systemdatabases)/(?P<dbname>\w+)/tables/(?P<tbl_name>\w+)/indexes/$'): RoutingTarget(
        None, 
        _indexes
    ),
    # Clicked on on the Triggers Folder inside of one particular table or view node
    re.compile(r'^/(?P<db>databases|systemdatabases)/(?P<dbname>\w+)/(?P<obj>tables|views)/(?P<tbl_name>\w+)/columns/$'): RoutingTarget(
        None,
        _columns
    ),
    # Clicked on on the Triggers Folder inside of one particular table or view node
    re.compile(r'^/(?P<db>databases|systemdatabases)/(?P<dbname>\w+)/(?P<obj>tables|views)/(?P<tbl_name>\w+)/triggers/$'): RoutingTarget(
        None,
        _triggers
    ),
    # Clicked on the Character Sets folder
    re.compile(r'^/charsets/$'): RoutingTarget(
       None,
        _charsets
    ),
    # Clicked on one particular charset node
    re.compile(r'^/charsets/(?P<charid>\d+)/$'): RoutingTarget(
        None, 
        _collations
    ),
    # Clicked on the Roles folder
    re.compile(r'^/users/$'): RoutingTarget(
        None, 
        _users
    ),
    # Clicked on the Tablespaces folder
    re.compile(r'^/tablespaces/$'): RoutingTarget(
        None, 
        _tablespaces
    )
}
