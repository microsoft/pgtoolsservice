# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from collections.abc import Generator
from typing import Any, Optional, TypeVar, Union
from urllib.parse import urljoin

from ossdbtoolsservice.metadata.contracts import ObjectMetadata
from ossdbtoolsservice.object_explorer.contracts import NodeInfo
from ossdbtoolsservice.object_explorer.session import (
    Folder,
    ObjectExplorerSession,
    RoutingTarget,
)
from pgsmo import Schema, Table, View
from smo.common.node_object import NodeObject

N = TypeVar("N", bound=NodeObject)

# NODE GENERATOR HELPERS ###################################################


def _get_node_schema(node: NodeObject) -> str | None:
    """Some nodes have a schema property, which is used below.
    This will return if it exists."""
    return getattr(node, "schema", None)


def _get_node_info(
    node: NodeObject,
    current_path: str,
    node_type: str,
    label: Optional[str] = None,
    is_leaf: bool = True,
) -> NodeInfo:
    """
    Utility method for generating a NodeInfo from a NodeObject
    :param node: NodeObject to convert into a NodeInfo.
                 node.name will be used for the label of the node (unless label is provided)
                 node.oid will be appended to the end of the
                 current URI to create the node's path
    :param current_path: URI provided in the request to expand/refresh
    :param node_type: Node type, determines icon used in UI
    :param label: Overrides the node.name is provided, display name of the
                    node displayed as-is
    :param is_leaf: Whether or not the node is a leaf. Default is true.
                    If false, a trailing slash
                    will be added to the node path to indicate it behaves as a folder
    :return: NodeInfo based on the NodeObject provided
    """
    # Generate the object metadata
    metadata = ObjectMetadata(node.urn, None, type(node).__name__, node.name, None)

    # Add the schema name if it is the immediate parent
    if node.parent is not None and node.parent.parent is None:
        node_schema = _get_node_schema(node)
        if node_schema is not None:
            metadata.schema = node_schema

    # Else if it is a table object, add the schema and the object name.
    # Important for scripting purposes
    # node.parent = Table/View, node.parent.parent = Schema, node.parent.parent.parent = None
    elif (
        node.parent is not None
        and node.parent.parent is not None
        and node.parent.parent.parent is None
    ):
        parent_schema = _get_node_schema(node.parent)
        if parent_schema is not None:
            metadata.schema = ".".join([parent_schema, node.parent.name])

    # Build the path to the node. Trailing slash is added to indicate URI is a folder
    trailing_slash = "" if is_leaf else "/"
    node_path = urljoin(current_path, str(node.oid) + trailing_slash)

    node_info: NodeInfo = NodeInfo(
        label=label if label is not None else node.name,
        node_path=node_path,
        node_type=node_type,
        metadata=metadata,
        is_leaf=is_leaf,
    )

    return node_info


def _get_obj_with_refresh(parent_obj: N, is_refresh: bool) -> N:
    if is_refresh:
        parent_obj.refresh()
    return parent_obj


def _get_schema(session: ObjectExplorerSession, dbid: Any, scid: Any) -> Schema:
    """Utility method to get a schema from the selected database from the collection"""
    return session.server.databases[int(dbid)].schemas[int(scid)]


def _get_schema_child_object(
    is_refresh: bool,
    current_path: str,
    session: ObjectExplorerSession,
    match_params: dict,
    node_type: str,
    schema_propname: str,
) -> list[NodeInfo]:
    schema = _get_obj_with_refresh(
        _get_schema(session, match_params["dbid"], match_params["scid"]), is_refresh
    )
    child_objects = getattr(schema, schema_propname)
    return [_get_node_info(node, current_path, node_type) for node in child_objects]


def _get_table_or_view(
    is_refresh: bool, session: ObjectExplorerSession, dbid: Any, parent_type: str, tid: Any
) -> Union[Table, View]:
    tid = int(tid)
    if parent_type == "tables":
        return _get_obj_with_refresh(
            session.server.databases[int(dbid)].tables[tid], is_refresh
        )
    elif parent_type == "views":
        return _get_obj_with_refresh(
            session.server.databases[int(dbid)].views[tid], is_refresh
        )
    elif parent_type == "materializedviews":
        return _get_obj_with_refresh(
            session.server.databases[int(dbid)].materialized_views[tid], is_refresh
        )
    else:
        # TODO: Localize
        raise ValueError("Object type to retrieve nodes is invalid")


# NODE GENERATORS ##########################################################
def _default_node_generator(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> list[NodeInfo]:
    """
    Clears cached Object Explorer Node information so that the refreshed node and
    its children fetches the data again when expanded
    """
    if is_refresh and session.server is not None:
        session.server.refresh()
    return []


def is_system_request(route_path: str) -> bool:
    return "/system/" in route_path


# FIRST TIER ##########################################################
def _roles(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> Generator[NodeInfo, Any, None]:
    """Function to generate a list of roles for a server"""
    _default_node_generator(is_refresh, current_path, session, match_params)
    for role in session.server.roles:
        node_type = "ServerLevelLogin" if role.can_login else "ServerLevelLogin_Disabled"
        yield _get_node_info(role, current_path, node_type)


def _tablespaces(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> list[NodeInfo]:
    """Function to generate a list of tablespaces for a server"""
    _default_node_generator(is_refresh, current_path, session, match_params)
    tablespaces = session.server.tablespaces
    return [_get_node_info(node, current_path, "Queue") for node in tablespaces]


def _databases(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> list[NodeInfo]:
    """Function to generate a list of databases"""
    _default_node_generator(is_refresh, current_path, session, match_params)
    is_system = "systemdatabase" in current_path
    return [
        _get_node_info(node, current_path, "Database", is_leaf=False)
        for node in session.server.databases
        if node.can_connect and node.is_system == is_system
    ]


# DATABASE LEAVES ##########################################################
def _views(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> list[NodeInfo]:
    """
    Function to generate a list of NodeInfo for views in a schema
    Expected match_params:
      scid int: schema OID
    """
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(
        session.server.databases[int(match_params["dbid"])], is_refresh
    )
    schema = _get_obj_with_refresh(
        _get_schema(session, match_params["dbid"], match_params["scid"]), is_refresh
    )
    return [
        _get_node_info(node, current_path, "View", label=f"{node.name}", is_leaf=False)
        for node in parent_obj.views
        if node.is_system == is_system and schema.name == node.schema
    ]


def _materialized_views(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> list[NodeInfo]:
    """
    Function to generate a list of NodeInfo for materialized views in a schema
    Expected match_params:
      scid int: schema OID
    """
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(
        session.server.databases[int(match_params["dbid"])], is_refresh
    )
    schema = _get_obj_with_refresh(
        _get_schema(session, match_params["dbid"], match_params["scid"]), is_refresh
    )
    return [
        _get_node_info(node, current_path, "View", label=f"{node.name}", is_leaf=False)
        for node in parent_obj.materialized_views
        if node.is_system == is_system and schema.name == node.schema
    ]


def _functions(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> list[NodeInfo]:
    """
    Function to generate a list of NodeInfo for functions in a schema
    Expected match_params:
      dbid int: Database OID
    """
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(
        session.server.databases[int(match_params["dbid"])], is_refresh
    )
    schema = _get_obj_with_refresh(
        _get_schema(session, match_params["dbid"], match_params["scid"]), is_refresh
    )
    return [
        _get_node_info(node, current_path, "ScalarValuedFunction", label=f"{node.name}")
        for node in parent_obj.functions
        if node.is_system == is_system and schema.name == node.schema
    ]


def _procedures(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> list[NodeInfo]:
    """
    Function to generate a list of NodeInfo for functions in a schema
    Expected match_params:
      dbid int: Database OID
    """
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(
        session.server.databases[int(match_params["dbid"])], is_refresh
    )
    schema = _get_obj_with_refresh(
        _get_schema(session, match_params["dbid"], match_params["scid"]), is_refresh
    )
    return [
        _get_node_info(node, current_path, "StoredProcedure", label=f"{node.name}")
        for node in parent_obj.procedures
        if node.is_system == is_system and schema.name == node.schema
    ]


def _trigger_functions(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> list[NodeInfo]:
    """
    Function to generate a list of NodeInfo for trigger functions in a schema
    Expected match_params:
      dbid int: Database OID
    """
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(
        session.server.databases[int(match_params["dbid"])], is_refresh
    )
    schema = _get_obj_with_refresh(
        _get_schema(session, match_params["dbid"], match_params["scid"]), is_refresh
    )
    return [
        _get_node_info(node, current_path, "TableValuedFunction", label=f"{node.name}")
        for node in parent_obj.trigger_functions
        if node.is_system == is_system and schema.name == node.schema
    ]


def _collations(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> list[NodeInfo]:
    """
    Function to generate a list of NodeInfo for collations in a schema
    Expected match_params:
      dbid int: Database OID
    """
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(
        session.server.databases[int(match_params["dbid"])], is_refresh
    )
    schema = _get_obj_with_refresh(
        _get_schema(session, match_params["dbid"], match_params["scid"]), is_refresh
    )
    return [
        _get_node_info(node, current_path, "collations", label=f"{node.name}")
        for node in parent_obj.collations
        if node.is_system == is_system and schema.name == node.schema
    ]


def _datatypes(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> list[NodeInfo]:
    """
    Function to generate a list of NodeInfo for datatypes in a schema
    Expected match_params:
      dbid int: Database OID
    """
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(
        session.server.databases[int(match_params["dbid"])], is_refresh
    )
    schema = _get_obj_with_refresh(
        _get_schema(session, match_params["dbid"], match_params["scid"]), is_refresh
    )
    return [
        _get_node_info(node, current_path, "Datatypes", label=f"{node.name}")
        for node in parent_obj.datatypes
        if node.is_system == is_system and schema.name == node.schema
    ]


def _sequences(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> list[NodeInfo]:
    """
    Function to generate a list of NodeInfo for sequences in a schema
    Expected match_params:
      dbid int: Database OID
    """
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(
        session.server.databases[int(match_params["dbid"])], is_refresh
    )
    schema = _get_obj_with_refresh(
        _get_schema(session, match_params["dbid"], match_params["scid"]), is_refresh
    )
    return [
        _get_node_info(node, current_path, "Sequence", label=f"{node.name}")
        for node in parent_obj.sequences
        if node.is_system == is_system and schema.name == node.schema
    ]


def _extensions(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> list[NodeInfo]:
    """
    Function to generate a list of NodeInfo for extensions in a schema
    Expected match_params:
      dbid int: Database OID
    """
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(
        session.server.databases[int(match_params["dbid"])], is_refresh
    )
    schema = _get_obj_with_refresh(
        _get_schema(session, match_params["dbid"], match_params["scid"]), is_refresh
    )
    return [
        _get_node_info(node, current_path, "extension", label=f"{node.name}")
        for node in parent_obj.extensions
        if node.is_system == is_system and schema.name == node.schema
    ]


def _schemas(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> list[NodeInfo]:
    """Function to generate a list of NodeInfo for tables in a schema"""
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(
        session.server.databases[int(match_params["dbid"])], is_refresh
    )
    return [
        _get_node_info(node, current_path, "Schema", is_leaf=False)
        for node in parent_obj.schemas
        if node.is_system == is_system
    ]


# SCHEMA LEAVES ##########################################################
def _tables(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> list[NodeInfo]:
    """
    Function to generate a list of NodeInfo for tables in a schema
    Expected match_params:
      dbid int: Database OID
    """
    is_system = is_system_request(current_path)
    parent_obj = _get_obj_with_refresh(
        session.server.databases[int(match_params["dbid"])], is_refresh
    )
    schema = _get_obj_with_refresh(
        _get_schema(session, match_params["dbid"], match_params["scid"]), is_refresh
    )
    return [
        _get_node_info(node, current_path, "Table", is_leaf=False, label=f"{node.name}")
        for node in parent_obj.tables
        if node.is_system == is_system and schema.name == node.schema
    ]


# TABLE LEAVES ##########################################################
def _columns(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> Generator[NodeInfo, Any, None]:
    """
    Function to generate column NodeInfo for tables/views
      dbid int: Database OID
      obj str: Type of the object to get columns from
      tid int: table or view OID
    """
    obj = _get_table_or_view(
        is_refresh, session, match_params["dbid"], match_params["obj"], match_params["tid"]
    )
    for column in obj.columns:
        label = f"{column.name} ({column.datatype})"
        yield _get_node_info(column, current_path, "Column", label=label)


def _constraints(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> list[NodeInfo]:
    """
    Function to generate constraint NodeInfo for tables
      dbid int: Database OID
      tid int: Table or View OID
    """
    table = _get_obj_with_refresh(
        session.server.databases[int(match_params["dbid"])].tables[int(match_params["tid"])],
        is_refresh,
    )
    node_info = []
    node_info.extend(
        [_get_node_info(node, current_path, "Constraint") for node in table.check_constraints]
    )
    node_info.extend(
        [
            _get_node_info(node, current_path, "Constraint")
            for node in table.exclusion_constraints
        ]
    )
    node_info.extend(
        [
            _get_node_info(node, current_path, "Key_ForeignKey")
            for node in table.foreign_key_constraints
        ]
    )
    node_info.extend(
        [
            _get_node_info(node, current_path, "Key_PrimaryKey")
            for node in table.primary_key_constraints
        ]
    )
    node_info.extend(
        [
            _get_node_info(node, current_path, "Key_UniqueKey")
            for node in table.unique_key_constraints
        ]
    )

    return sorted(node_info, key=lambda x: x.label)


def _indexes(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> Generator[NodeInfo, Any, None]:
    """
    Function to generate index NodeInfo for tables
    Expected match_params:
      dbid int: Database OID
      tid int: table OID
    """
    parent_type = match_params["obj"]
    attribute_name = ""
    if parent_type == "tables":
        attribute_name = "tables"
    elif parent_type == "materializedviews":
        attribute_name = "materialized_views"
    else:
        raise ValueError("Object type to retrieve nodes is invalid")

    entities = getattr(session.server.databases[int(match_params["dbid"])], attribute_name)
    indexes = _get_obj_with_refresh(entities[int(match_params["tid"])].indexes, is_refresh)

    for index in indexes:
        attribs = ["Clustered" if index.is_clustered else "Non-Clustered"]
        # TODO: Add back in the correct node_type, but making sure the SCRIPT AS options
        # still appear in the right-click menu
        # if index.is_primary:
        #     node_type = 'Key_PrimaryKey'
        if index.is_unique:
            # node_type = 'Key_UniqueKey'
            attribs.insert(0, "Unique")
        node_type = "Index"

        attrib_str = "(" + ", ".join(attribs) + ")"
        yield _get_node_info(
            index, current_path, node_type, label=f"{index.name} {attrib_str}"
        )


def _rules(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> list[NodeInfo]:
    """
    Function to generate a list of rules for tables and views
    Expected match_params:
      scid int: schema OID
      obj str: parent object to lookup (table or view)
      tid int: table or view OID
    """
    obj = _get_table_or_view(
        is_refresh, session, match_params["dbid"], match_params["obj"], match_params["tid"]
    )
    # TODO: We need a better icon for rules
    return [_get_node_info(rule, current_path, "Constraint") for rule in obj.rules]


def _triggers(
    is_refresh: bool, current_path: str, session: ObjectExplorerSession, match_params: dict
) -> list[NodeInfo]:
    """Function to generate a list of triggers for a table or view"""
    parent_obj = _get_table_or_view(
        is_refresh, session, match_params["dbid"], match_params["obj"], match_params["tid"]
    )
    return [_get_node_info(node, current_path, "Trigger") for node in parent_obj.triggers]


# ROUTING TABLE ############################################################
# This is the table that maps a regular expression to a routing target.
# When using route_request,
# the regular expression will be matched with the provided path.
# The routing target will then be
# used to generate a list of nodes that belong under the node. This can be a list of folders,
# a list of nodes generated by a function, or both.
# REGEX NOTES: (?P<name>...) is a named capture group
# (see https://docs.python.org/2/library/re.html#regular-expression-syntax)

PG_ROUTING_TABLE = {
    re.compile(r"^/$"): RoutingTarget(
        [
            Folder("Databases", "databases"),
            Folder("System Databases", "systemdatabases"),
            Folder("Roles", "roles"),
            Folder("Tablespaces", "tablespaces"),
        ],
        _default_node_generator,
    ),
    re.compile(r"^/(?P<db>databases|systemdatabases)/$"): RoutingTarget(None, _databases),
    re.compile(r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/$"): RoutingTarget(
        [Folder("Schemas", "schemas")], _default_node_generator
    ),
    re.compile(r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/$"): RoutingTarget(
        [Folder("System", "system")], _schemas
    ),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/$"
    ): RoutingTarget(None, _schemas),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/$"
    ): RoutingTarget(
        [
            Folder("Tables", "tables"),
            Folder("Views", "views"),
            Folder("Materialized Views", "materializedviews"),
            Folder("Functions", "functions"),
            Folder("Procedures", "procedures"),
            Folder("Trigger Functions", "triggerfunctions"),
            Folder("Collations", "collations"),
            Folder("Data Types", "datatypes"),
            Folder("Sequences", "sequences"),
            Folder("Extensions", "extensions"),
        ],
        _default_node_generator,
    ),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/$"
    ): RoutingTarget(
        [
            Folder("Tables", "tables"),
            Folder("Views", "views"),
            Folder("Materialized Views", "materializedviews"),
            Folder("Functions", "functions"),
            Folder("Procedures", "procedures"),
            Folder("Trigger Functions", "triggerfunctions"),
            Folder("Collations", "collations"),
            Folder("Data Types", "datatypes"),
            Folder("Sequences", "sequences"),
            Folder("Extensions", "extensions"),
        ],
        _default_node_generator,
    ),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/tables/$"
    ): RoutingTarget(None, _tables),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/tables/$"
    ): RoutingTarget(None, _tables),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/views/$"
    ): RoutingTarget(None, _views),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/views/$"
    ): RoutingTarget(None, _views),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/materializedviews/$"
    ): RoutingTarget(None, _materialized_views),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/materializedviews/$"
    ): RoutingTarget(None, _materialized_views),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/functions/$"
    ): RoutingTarget(None, _functions),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/functions/$"
    ): RoutingTarget(None, _functions),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/procedures/$"
    ): RoutingTarget(None, _procedures),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/procedures/$"
    ): RoutingTarget(None, _procedures),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/triggerfunctions/$"
    ): RoutingTarget(None, _trigger_functions),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/triggerfunctions/$"
    ): RoutingTarget(None, _trigger_functions),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/collations/$"
    ): RoutingTarget(None, _collations),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/collations/$"
    ): RoutingTarget(None, _collations),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/datatypes/$"
    ): RoutingTarget(None, _datatypes),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/datatypes/$"
    ): RoutingTarget(None, _datatypes),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/sequences/$"
    ): RoutingTarget(None, _sequences),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/sequences/$"
    ): RoutingTarget(None, _sequences),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/extensions/$"
    ): RoutingTarget(None, _extensions),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/extensions/$"
    ): RoutingTarget(None, _extensions),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/tables/(?P<tid>\d+)/$"
    ): RoutingTarget(
        [
            Folder("Columns", "columns"),
            Folder("Constraints", "constraints"),
            Folder("Indexes", "indexes"),
            Folder("Rules", "rules"),
            Folder("Triggers", "triggers"),
        ],
        _default_node_generator,
    ),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/tables/(?P<tid>\d+)/$"
    ): RoutingTarget(
        [
            Folder("Columns", "columns"),
            Folder("Constraints", "constraints"),
            Folder("Indexes", "indexes"),
            Folder("Rules", "rules"),
            Folder("Triggers", "triggers"),
        ],
        _default_node_generator,
    ),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/views/(?P<vid>\d+/$)"
    ): RoutingTarget(
        [
            Folder("Columns", "columns"),
            Folder("Rules", "rules"),
            Folder("Triggers", "triggers"),
        ],
        _default_node_generator,
    ),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/views/(?P<vid>\d+/$)"
    ): RoutingTarget(
        [
            Folder("Columns", "columns"),
            Folder("Rules", "rules"),
            Folder("Triggers", "triggers"),
        ],
        _default_node_generator,
    ),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/materializedviews/(?P<vid>\d+/$)"
    ): RoutingTarget(
        [Folder("Columns", "columns"), Folder("Indexes", "indexes")], _default_node_generator
    ),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/materializedviews/(?P<vid>\d+/$)"
    ): RoutingTarget(
        [Folder("Columns", "columns"), Folder("Indexes", "indexes")], _default_node_generator
    ),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/(?P<obj>tables|views|materializedviews)/(?P<tid>\d+)/columns/$"
    ): RoutingTarget(None, _columns),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/(?P<obj>tables|views|materializedviews)/(?P<tid>\d+)/columns/$"
    ): RoutingTarget(None, _columns),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/tables/(?P<tid>\d+)/constraints/$"
    ): RoutingTarget(None, _constraints),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/tables/(?P<tid>\d+)/constraints/$"
    ): RoutingTarget(None, _constraints),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/(?P<obj>tables|materializedviews)/(?P<tid>\d+)/indexes/$"
    ): RoutingTarget(None, _indexes),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/(?P<obj>tables|materializedviews)/(?P<tid>\d+)/indexes/$"
    ): RoutingTarget(None, _indexes),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/(?P<obj>tables|views)/(?P<tid>\d+)/rules/$"
    ): RoutingTarget(None, _rules),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/(?P<obj>tables|views)/(?P<tid>\d+)/rules/$"
    ): RoutingTarget(None, _rules),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/(?P<scid>\d+)/(?P<obj>tables|views)/(?P<tid>\d+)/triggers/$"
    ): RoutingTarget(None, _triggers),
    re.compile(
        r"^/(?P<db>databases|systemdatabases)/(?P<dbid>\d+)/schemas/system/(?P<scid>\d+)/(?P<obj>tables|views)/(?P<tid>\d+)/triggers/$"
    ): RoutingTarget(None, _triggers),
    re.compile(r"^/roles/$"): RoutingTarget(None, _roles),
    re.compile(r"^/tablespaces/$"): RoutingTarget(None, _tablespaces),
}
