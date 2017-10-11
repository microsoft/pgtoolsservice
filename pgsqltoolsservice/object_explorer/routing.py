# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from typing import Callable, List, Optional, TypeVar, Union
from urllib.parse import urljoin, urlparse

from pgsmo import NodeObject, Schema, Table, View
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
    TNodeGenerator = TypeVar(Optional[Callable[[bool, str, ObjectExplorerSession, dict], List[NodeInfo]]])

    def __init__(self, folders: Optional[List[Folder]], node_generator: TNodeGenerator):
        """
        Initializes a routing target
        :param folders: A list of folders to return at the top of the expanded node results
        :param node_generator: A function that generates a list of nodes to show in the expanded results
        """
        self.folders: List[Folder] = folders or []
        self.node_generator = node_generator

    def get_nodes(self, is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
        """
        Builds a list of NodeInfo that should be displayed under the current routing path
        :param is_refresh: Whether or not the nodes should be refreshed before retrieval
        :param current_path: The requested node path
        :param session: OE Session that the lookup will be performed from
        :param match_params: The captures from the regex that this routing target is mapped from
        :return: A list of NodeInfo
        """
        # Start by adding the static folders
        folder_nodes = [folder.as_node(current_path) for folder in self.folders]

        # Execute the node generator to generate the non-static nodes and add them after the folders
        if self.node_generator is not None:
            nodes = self.node_generator(is_refresh, current_path, session, match_params)
            folder_nodes.extend(nodes)

        return folder_nodes


# NODE GENERATOR HELPERS ###################################################
def _get_node_info(
        node: NodeObject,
        current_path: str,
        node_type: str,
        label: Optional[str]=None,
        is_leaf: bool=True
) -> NodeInfo:
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
    node_info.node_path = urljoin(current_path, str(node.oid) + trailing_slash)

    return node_info


TRefreshObject = TypeVar('NodeObject')


def _get_obj_with_refresh(parent_obj: TRefreshObject, is_refresh: bool) -> TRefreshObject:
    if is_refresh:
        parent_obj.refresh()
    return parent_obj


def _get_schema(session: ObjectExplorerSession, dbid: any, scid: any) -> Schema:
    """Utility method to get a schema from the selected database from the collection"""
    return session.server.databases[int(dbid)].schemas[int(scid)]


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
    obj = _get_table_or_view(is_refresh, session, match_params['dbid'], match_params['obj'], match_params['tid'])
    for column in obj.columns:
        label = f'{column.name} ({column.datatype})'
        yield _get_node_info(column, current_path, 'Column', label=label)


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
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(session.server.databases[int(match_params['dbid'])], is_refresh)
    return [
        _get_node_info(node, current_path, 'ScalarValuedFunction', label=f'{node.schema}.{node.name}')
        for node in parent_obj.functions if node.is_system == is_system
    ]


def _collations(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for collations in a schema
    Expected match_params:
      dbid int: Database OID
    """
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(session.server.databases[int(match_params['dbid'])], is_refresh)
    return [
        _get_node_info(node, current_path, 'collations', label=f'{node.schema}.{node.name}')
        for node in parent_obj.collations if node.is_system == is_system
    ]


def _datatypes(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for datatypes in a schema
    Expected match_params:
      dbid int: Database OID
    """
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(session.server.databases[int(match_params['dbid'])], is_refresh)
    return [
        _get_node_info(node, current_path, 'Datatypes', label=f'{node.schema}.{node.name}')
        for node in parent_obj.datatypes if node.is_system == is_system
    ]


def _sequences(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for sequences in a schema
    Expected match_params:
      dbid int: Database OID
    """
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(session.server.databases[int(match_params['dbid'])], is_refresh)
    return [
        _get_node_info(node, current_path, 'Sequence', label=f'{node.schema}.{node.name}')
        for node in parent_obj.sequences if node.is_system == is_system
    ]


def _get_schema_child_object(is_refresh: bool, current_path: str, session: ObjectExplorerSession,
                             match_params: dict, node_type: str, schema_propname: str) -> List[NodeInfo]:
    schema = _get_obj_with_refresh(_get_schema(session, match_params['dbid'], match_params['scid']), is_refresh)
    child_objects = getattr(schema, schema_propname)
    return [
        _get_node_info(node, current_path, node_type)
        for node in child_objects
    ]


def _indexes(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate index NodeInfo for tables
    Expected match_params:
      dbid int: Database OID
      tid int: table OID
    """
    parent_type = match_params['obj']
    attribute_name = ''
    if parent_type == 'tables':
        attribute_name = 'tables'
    elif parent_type == 'materializedviews':
        attribute_name = 'materialized_views'
    else:
        raise ValueError('Object type to retrieve nodes is invalid')

    entities = getattr(session.server.databases[int(match_params['dbid'])], attribute_name)
    indexes = _get_obj_with_refresh(entities[int(match_params['tid'])].indexes, is_refresh)

    for index in indexes:
        attribs = ['Clustered' if index.is_clustered else 'Non-Clustered']
        if index.is_primary:
            node_type = 'Key_PrimaryKey'
        elif index.is_unique:
            node_type = 'Key_UniqueKey'
            attribs.insert(0, 'Unique')
        else:
            node_type = 'Index'

        attrib_str = '(' + ', '.join(attribs) + ')'
        yield _get_node_info(index, current_path, node_type, label=f'{index.name} {attrib_str}')


def is_system_request(route_path: str):
    return '/system/' in route_path


def _tables(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for tables in a schema
    Expected match_params:
      dbid int: Database OID
    """
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(session.server.databases[int(match_params['dbid'])], is_refresh)
    return [
        _get_node_info(node, current_path, 'Table', is_leaf=False, label=f'{node.schema}.{node.name}')
        for node in parent_obj.tables if node.is_system == is_system
    ]


def _roles(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """Function to generate a list of roles for a server"""
    if is_refresh:
        session.server.refresh()
    for role in session.server.roles:
        node_type = "ServerLevelLogin" if role.can_login else "ServerLevelLogin_Disabled"
        yield _get_node_info(role, current_path, node_type)


def _rules(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of rules for tables and views
    Expected match_params:
      scid int: schema OID
      obj str: parent object to lookup (table or view)
      tid int: table or view OID
    """
    obj = _get_table_or_view(is_refresh, session, match_params['dbid'], match_params['obj'], match_params['tid'])
    # TODO: We need a better icon for rules
    return [_get_node_info(rule, current_path, 'Constraint') for rule in obj.rules]


def _schemas(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """Function to generate a list of NodeInfo for tables in a schema"""
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(session.server.databases[int(match_params['dbid'])], is_refresh)
    return [_get_node_info(node, current_path, 'Schema', is_leaf=True) for node in parent_obj.schemas if node.is_system == is_system]


def _databases(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """Function to generate a list of databases"""
    if is_refresh:
        session.server.refresh()
    is_system = 'systemdatabase' in current_path
    return [_get_node_info(node, current_path, 'Database', is_leaf=False)
            for node in session.server.databases if node.can_connect and node.is_system == is_system]


def _tablespaces(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """Function to generate a list of tablespaces for a server"""
    if is_refresh:
        session.server.refresh()
    tablespaces = session.server.tablespaces
    return [_get_node_info(node, current_path, 'Queue') for node in tablespaces]


def _triggers(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """Function to generate a list of triggers for a table or view"""
    parent_obj = _get_table_or_view(is_refresh, session, match_params['dbid'], match_params['obj'], match_params['tid'])
    return [_get_node_info(node, current_path, 'Trigger') for node in parent_obj.triggers]


def _views(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for views in a schema
    Expected match_params:
      scid int: schema OID
    """
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(session.server.databases[int(match_params['dbid'])], is_refresh)
    return [_get_node_info(node, current_path, 'View', label=f'{node.schema}.{node.name}', is_leaf=False)
            for node in parent_obj.views if node.is_system == is_system]


def _materialized_views(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for materialized views in a schema
    Expected match_params:
      scid int: schema OID
    """
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(session.server.databases[int(match_params['dbid'])], is_refresh)
    return [_get_node_info(node, current_path, 'View', label=f'{node.schema}.{node.name}', is_leaf=False)
            for node in parent_obj.materialized_views if node.is_system == is_system]


def _extensions(is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict) -> List[NodeInfo]:
    """
    Function to generate a list of NodeInfo for extensions in a schema
    Expected match_params:
      dbid int: Database OID
    """
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(session.server.databases[int(match_params['dbid'])], is_refresh)
    return [
        _get_node_info(node, current_path, 'extension', label=f'{node.schema}.{node.name}')
        for node in parent_obj.extensions if node.is_system == is_system
    ]


# ROUTING TABLE ############################################################
# This is the table that maps a regular expression to a routing target. When using route_request,
# the regular expression will be matched with the provided path. The routing target will then be
# used to generate a list of nodes that belong under the node. This can be a list of folders,
# a list of nodes generated by a function, or both.
# REGEX NOTES: (?P<name>...) is a named capture group
# (see https://docs.python.org/2/library/re.html#regular-expression-syntax)

ROUTING_TABLE = {
    re.compile('^/$'): RoutingTarget(
        [
            Folder('Databases', 'databases'),
            Folder('System Databases', 'systemdatabases'),
            Folder('Roles', 'roles'),
            Folder('Tablespaces', 'tablespaces')
        ],
        None
    ),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/$'): RoutingTarget(
        [
            Folder('Tables', 'tables'),
            Folder('Views', 'views'),
            Folder('Materialized Views', 'materializedviews'),
            Folder('Functions', 'functions'),
            Folder('Collations', 'collations'),
            Folder('Data Types', 'datatypes'),
            Folder('Sequences', 'sequences'),
            Folder('Schemas', 'schemas'),
            Folder('Extensions', 'extensions')
        ],
        None
    ),
    re.compile('^/(?P<db>databases|systemdatabases)/$'): RoutingTarget(None, _databases),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/tables/$'): RoutingTarget(
        [
            Folder('System', 'system')
        ],
        _tables
    ),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/tables/system/$'): RoutingTarget(None, _tables),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/views/$'): RoutingTarget(
        [
            Folder('System', 'system')
        ],
        _views
    ),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/views/system/$'): RoutingTarget(None, _views),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/materializedviews/$'): RoutingTarget(
        [
            Folder('System', 'system')
        ],
        _materialized_views
    ),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/materializedviews/system/$'): RoutingTarget(None, _materialized_views),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/functions/$'): RoutingTarget(
        [
            Folder('System', 'system')
        ],
        _functions
    ),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/functions/system/$'): RoutingTarget(None, _functions),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/collations/$'): RoutingTarget(
        [
            Folder('System', 'system')
        ],
        _collations
    ),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/collations/system/$'): RoutingTarget(None, _collations),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/datatypes/$'): RoutingTarget(
        [
            Folder('System', 'system')
        ],
        _datatypes
    ),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/datatypes/system/$'): RoutingTarget(None, _datatypes),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/sequences/$'): RoutingTarget(
        [
            Folder('System', 'system')
        ],
        _sequences
    ),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/sequences/system/$'): RoutingTarget(None, _sequences),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/$'): RoutingTarget(
        [
            Folder('System', 'system')
        ],
        _schemas
    ),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/$'): RoutingTarget(None, _schemas),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/tables/(?P<tid>\d+)/$'): RoutingTarget(
        [
            Folder('Columns', 'columns'),
            Folder('Constraints', 'constraints'),
            Folder('Indexes', 'indexes'),
            Folder('Rules', 'rules'),
            Folder('Triggers', 'triggers')
        ],
        None
    ),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/tables/system/(?P<tid>\d+)/$'): RoutingTarget(
        [
            Folder('Columns', 'columns'),
            Folder('Constraints', 'constraints'),
            Folder('Indexes', 'indexes'),
            Folder('Rules', 'rules'),
            Folder('Triggers', 'triggers')
        ],
        None
    ),
    re.compile(
        '^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/(?P<obj>tables|views|materializedviews)/(?P<tid>\d+)/columns/$'
    ): RoutingTarget(None, _columns),
    re.compile(
        '^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/(?P<obj>tables|views|materializedviews)/system/(?P<tid>\d+)/columns/$'
    ): RoutingTarget(None, _columns),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/tables/(?P<tid>\d+)/constraints/$'): RoutingTarget(None, _constraints),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/tables/system/(?P<tid>\d+)/constraints/$'): RoutingTarget(None, _constraints),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/(?P<obj>tables|materializedviews)/(?P<tid>\d+)/indexes/$'): RoutingTarget(None, _indexes),
    re.compile(
        '^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/(?P<obj>tables|materializedviews)/system/(?P<tid>\d+)/indexes/$'
    ): RoutingTarget(None, _indexes),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/(?P<obj>tables|views)/(?P<tid>\d+)/rules/$'): RoutingTarget(None, _rules),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/(?P<obj>tables|views)/system/(?P<tid>\d+)/rules/$'): RoutingTarget(None, _rules),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/(?P<obj>tables|views)/(?P<tid>\d+)/triggers/$'): RoutingTarget(None, _triggers),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/(?P<obj>tables|views)/system/(?P<tid>\d+)/triggers/$'): RoutingTarget(None, _triggers),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/views/(?P<vid>\d+/$)'): RoutingTarget(
        [
            Folder('Columns', 'columns'),
            Folder('Rules', 'rules'),
            Folder('Triggers', 'triggers')
        ],
        None
    ),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/views/system/(?P<vid>\d+/$)'): RoutingTarget(
        [
            Folder('Columns', 'columns'),
            Folder('Rules', 'rules'),
            Folder('Triggers', 'triggers')
        ],
        None
    ),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/materializedviews/(?P<vid>\d+/$)'): RoutingTarget(
        [
            Folder('Columns', 'columns'),
            Folder('Indexes', 'indexes')
        ],
        None
    ),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/materializedviews/system/(?P<vid>\d+/$)'): RoutingTarget(
        [
            Folder('Columns', 'columns'),
            Folder('Indexes', 'indexes')
        ],
        None
    ),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/functions(/system)/$'): RoutingTarget(None, _functions),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/collations(/system)/$'): RoutingTarget(None, _collations),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/datatypes(/system)/$'): RoutingTarget(None, _datatypes),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/sequences(/system)/$'): RoutingTarget(None, _sequences),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/extensions/$'): RoutingTarget(
        [
            Folder('System', 'system')
        ],
        _extensions
    ),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/extensions/system/$'): RoutingTarget(None, _extensions),
    re.compile('^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/extensions/system/$'): RoutingTarget(None, _extensions),
    re.compile('^/roles/$'): RoutingTarget(None, _roles),
    re.compile('^/tablespaces/$'): RoutingTarget(None, _tablespaces)
}


# PUBLIC FUNCTIONS #########################################################


def route_request(is_refresh: bool, session: ObjectExplorerSession, path: str) -> List[NodeInfo]:
    """
    Performs a lookup for a given expand request
    :param is_refresh: Whether or not the request is a request to refresh or just expand
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
            return target.get_nodes(is_refresh, path, session, match.groupdict())

    # If we make it to here, there isn't a route that matches the path
    raise ValueError(f'Path {path} does not have a matching OE route')  # TODO: Localize
