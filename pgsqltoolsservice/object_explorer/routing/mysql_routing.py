# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from urllib.parse import urljoin, urlparse
from typing import Callable, Dict, List, Optional

from smo.common.node_object import NodeObject
from mysqlsmo import *
from pgsqltoolsservice.metadata.contracts import ObjectMetadata
from pgsqltoolsservice.object_explorer.session import ObjectExplorerSession, Folder, RoutingTarget
from pgsqltoolsservice.object_explorer.contracts import NodeInfo

SYSTEM_DATABASES = {"information_schema", "mysql", "performance_schema"}

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

    node_info: NodeInfo = NodeInfo()
    node_info.is_leaf = is_leaf
    node_info.label = label if label is not None else node.name
    node_info.metadata = metadata
    node_info.node_type = node_type

    # Build the path to the node. Trailing slash is added to indicate URI is a folder
    trailing_slash = '' if is_leaf else '/'
    node_info.node_path = urljoin(current_path, str(node.name) + trailing_slash)

    return node_info


# NODE GENERATORS ##########################################################
def _columns(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate column NodeInfo for tables/views
      dbid int: Database OID
      obj str: Type of the object to get columns from
      tid int: table or view OID
    """
    root_server=session.server
    nodes = Column.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'Column', label=f'{node.name}')
        for node in nodes
    ]


def _constraints(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate constraint NodeInfo for tables
      dbid int: Database OID
      tid int: Table or View OID
    """
    # Get all the types of constraints
    primary: List[NodeInfo] = _primary_keys(is_refresh, current_path, session, match_params)
    foreign: List[NodeInfo] = _foreign_keys(is_refresh, current_path, session, match_params)
    check: List[NodeInfo] = _check_constraints(is_refresh, current_path, session, match_params)
    unique: List[NodeInfo] = _unique_constraints(is_refresh, current_path, session, match_params)

    all_constraints: List[NodeInfo] = primary + foreign + check + unique
    return all_constraints

def _primary_keys(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    root_server=session.server
    nodes = PrimaryKeyConstraint.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'ColumnMasterKey', label=f'{node.name}')
        for node in nodes
    ]

def _foreign_keys(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    root_server=session.server
    nodes = ForeignKeyConstraint.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'ColumnEncryptionKey', label=f'{node.name}')
        for node in nodes
    ]

def _check_constraints(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    root_server=session.server
    nodes = CheckConstraint.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'Constraint', label=f'{node.name}')
        for node in nodes
    ]

def _unique_constraints(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    root_server=session.server
    nodes = UniqueConstraint.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'AsymmetricKey', label=f'{node.name}')
        for node in nodes
    ]


def _functions(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for functions in a schema
    Expected match_params:
      dbid int: Database OID
    """
    root_server=session.server
    nodes = Function.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'AggregateFunction', label=f'{node.name}')
        for node in nodes
    ]

def _procedures(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for functions in a schema
    Expected match_params:
      dbid int: Database OID
    """
    root_server=session.server
    nodes = Procedure.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'StoredProcedure', label=f'{node.name}')
        for node in nodes
    ]

def _collations(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for collations in a schema
    Expected match_params:
      dbid int: Database OID
    """
    root_server=session.server
    nodes = Collation.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'SystemOtherDataType', label=f'{node.name}')
        for node in nodes
    ]

def _charsets(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for character set in a schema
    Expected match_params:
      dbid int: Database OID
    """
    root_server=session.server
    nodes = CharacterSet.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'HistoryTable', label=f'{node.name}', is_leaf=False)
        for node in nodes
    ]


def _indexes(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate index NodeInfo for tables
    Expected match_params:
      dbid int: Database OID
      tid int: table OID
    """
    root_server=session.server
    nodes = Index.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'Index', label=f'{node.name}')
        for node in nodes
    ]


def _tables(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for tables in a schema
    Expected match_params:
      dbid int: Database OID
    """
    root_server=session.server
    nodes = Table.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'Table', label=f'{node.name}', is_leaf=False)
        for node in nodes
    ]


def _users(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """Function to generate a list of users for a server"""
    root_server=session.server
    nodes = User.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'User', label=f'{node.name}')
        for node in nodes
    ]

def _sysdatabases(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """Function to generate a list of databases"""
    root_server=session.server
    nodes = Database.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'Database', label=f'{node.name}', is_leaf=False)
        for node in nodes if node.name in SYSTEM_DATABASES
    ]

def _databases(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """Function to generate a list of databases"""
    root_server=session.server
    nodes = Database.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'Database', label=f'{node.name}', is_leaf=False)
        for node in nodes if node.name not in SYSTEM_DATABASES
    ]


def _tablespaces(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """Function to generate a list of tablespaces for a server"""
    root_server=session.server
    nodes = Tablespace.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'Queue', label=f'{node.name}')
        for node in nodes
    ]


def _triggers(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """Function to generate a list of triggers for a table or view"""
    root_server=session.server
    nodes = Trigger.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'DatabaseTrigger', label=f'{node.name}')
        for node in nodes
    ]


def _views(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for views in a schema
    Expected match_params:
      scid int: schema OID
    """
    root_server = session.server
    nodes = View.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'View', label=f'{node.name}', is_leaf=False)
        for node in nodes
    ]

def _events(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict):
    root_server=session.server
    nodes = Event.get_nodes_for_parent(root_server, parent_obj=None, context_args=match_params)
    return [
        _get_node_info(node, current_path, 'Statistic', label=f'{node.name}')
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
    # Clicked on the Events folder, should list event nodes
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
    # Clicked on on the Triggers Folder inside of one particular table, should list table trigger nodes
    re.compile(r'^/(?P<db>databases|systemdatabases)/(?P<dbname>\w+)/tables/(?P<tbl_name>\w+)/triggers/$'): RoutingTarget(
        None,
        _triggers
    ),
    # Clicked on the Character Sets folder
    re.compile(r'^/charsets/$'): RoutingTarget(
       None,
        _charsets
    ),
    # Clicked on one particular charset node, should show the Collations folder
    re.compile(r'^/charsets/(?P<char_name>\w+)/$'): RoutingTarget(
         [
            Folder('Collations', 'collations')
        ],
        _default_node_generator
    ),
    # Clicked on Collations folder for one particular charset node
    re.compile(r'^/charsets/(?P<char_name>\w+)/collations/$'): RoutingTarget(
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
