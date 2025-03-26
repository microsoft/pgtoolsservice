# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading
from collections.abc import Iterable
from typing import Callable, Optional
from urllib.parse import urljoin

from ossdbtoolsservice.connection.contracts import ConnectionDetails
from ossdbtoolsservice.object_explorer.contracts import NodeInfo
from pgsmo import Server


class ObjectExplorerSession:
    def __init__(self, session_id: str, params: ConnectionDetails) -> None:
        self.connection_details: ConnectionDetails = params
        self.id: str = session_id
        self.is_ready: bool = False
        self._server: Optional[Server] = None

        self.init_task: Optional[threading.Thread] = None
        self.expand_tasks: dict[str, threading.Thread] = {}
        self.refresh_tasks: dict[str, threading.Thread] = {}
        self.cache: dict[str, list[NodeInfo]] = {}

    @property
    def server(self) -> Server:
        if self._server is None:
            raise ValueError("Server not initialized")
        return self._server

    @server.setter
    def server(self, value: Server) -> None:
        self._server = value


class Folder:
    """Defines a folder that should be added to the top of a list of nodes"""

    def __init__(self, label: str, path: str):
        """
        Initializes a folder
        :param label: Display name of the folder (will be returned to the user as-is)
        :param path: URI component to add to the end of the current path.
                     A trailing slash will be added
                     Eg: If the path for the folder is oe://user@host:db/path/to/folder/ this
                     param should be 'folder'
        """
        self.label = label
        self.path = path + "/"

    def as_node(self, current_path: str) -> NodeInfo:
        """
        Generates a NodeInfo object that will represent the folder.
        :param current_path: The requested URI to expand/refresh
        :return: A non-leaf, folder node with the label and path from the object definition
        """
        node: NodeInfo = NodeInfo(
            label=self.label,
            node_path=urljoin(current_path, self.path),
            node_type="Folder",
            metadata=None,
            is_leaf=False,
        )
        return node


class RoutingTarget:
    """
    Represents the target of a route. Can contain a list of folders,
    a function that generates a list of nodes or both.
    """

    def __init__(
        self,
        folders: Optional[list[Folder]],
        node_generator: Callable[[bool, str, ObjectExplorerSession, dict], Iterable[NodeInfo]]
        | None,
    ) -> None:
        """
        Initializes a routing target
        :param folders: A list of folders to return at the top of the expanded node results
        :param node_generator: A function that generates a list of
            nodes to show in the expanded results. Takes in a
            current path, session, and parameters
            from the regular expression match and returns a list of NodeInfo objects.
        """
        self.folders: list[Folder] = folders or []
        self.node_generator = node_generator

    def get_nodes(
        self,
        is_refresh: bool,
        current_path: str,
        session: ObjectExplorerSession,
        match_params: dict,
    ) -> list[NodeInfo]:
        """
        Builds a list of NodeInfo that should be displayed under the current routing path
        :param is_refresh: Whether or not the nodes should be refreshed before retrieval
        :param current_path: The requested node path
        :param session: OE Session that the lookup will be performed from
        :param match_params: The captures from the regex that this
            routing target is mapped from
        :return: A list of NodeInfo
        """
        # Start by adding the static folders
        folder_nodes = [folder.as_node(current_path) for folder in self.folders]

        # Execute the node generator to generate the non-static nodes
        # and add them after the folders
        if self.node_generator is not None:
            nodes = self.node_generator(is_refresh, current_path, session, match_params)
            if nodes:
                folder_nodes.extend(nodes)

        return folder_nodes
