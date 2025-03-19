# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds the connection service class, which allows for the user to connect and
disconnect and holds the current connection, if one is present"""

import threading
from typing import Any, Callable, Optional

from ossdbtoolsservice.connection.contracts import (
    CANCEL_CONNECT_REQUEST,
    CONNECT_REQUEST,
    CONNECTION_COMPLETE_METHOD,
    DISCONNECT_REQUEST,
    LIST_DATABASES_REQUEST,
    AzureToken,
    CancelConnectParams,
    ChangeDatabaseRequestParams,
    ConnectionCompleteParams,
    ConnectionDetails,
    ConnectionType,
    ConnectRequestParams,
    DisconnectRequestParams,
    GetConnectionStringParams,
    ListDatabasesParams,
    ListDatabasesResponse,
)
from ossdbtoolsservice.connection.contracts.fetch_azure_token_request import (
    FETCH_AZURE_TOKEN_REQUEST_METHOD,
    FetchAzureTokenRequestParams,
)
from ossdbtoolsservice.connection.core.connection_manager import (
    ConnectionManager,
)
from ossdbtoolsservice.connection.core.errors import AzureTokenRefreshError
from ossdbtoolsservice.connection.core.owner_connection_info import OwnerConnectionInfo
from ossdbtoolsservice.connection.core.pooled_connection import PooledConnection
from ossdbtoolsservice.connection.core.server_connection import ServerConnection
from ossdbtoolsservice.hosting import RequestContext, Service, ServiceProvider
from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.workspace.workspace_service import WorkspaceService


class ConnectionService(Service):
    """Manage connections, including the ability to connect/disconnect"""

    def __init__(self, connection_manager: ConnectionManager | None = None) -> None:
        super().__init__()
        self._service_provider: ServiceProvider | None = None
        self._on_connect_callbacks: list[Callable[[OwnerConnectionInfo], None]] = []

        # Allow the connection manager to be injected for testing
        if connection_manager:
            self._connection_manager: ConnectionManager = connection_manager
            connection_manager.set_fetch_azure_token(self._fetch_azure_token)
        else:
            self._connection_manager = ConnectionManager(self._fetch_azure_token)

    def register(self, service_provider: ServiceProvider) -> None:
        self._service_provider = service_provider

        # Register the handlers for the service
        service_provider.server.set_request_handler(
            CONNECT_REQUEST, self.handle_connect_request
        )
        service_provider.server.set_request_handler(
            DISCONNECT_REQUEST, self.handle_disconnect_request
        )
        service_provider.server.set_request_handler(
            LIST_DATABASES_REQUEST, self.handle_list_databases
        )
        service_provider.server.set_request_handler(
            CANCEL_CONNECT_REQUEST, self.handle_cancellation_request
        )

        # Unused in VSCode
        # service_provider.server.set_request_handler(
        #     CHANGE_DATABASE_REQUEST, self.handle_change_database_request
        # )

        # This is unimplemented
        # service_provider.server.set_request_handler(
        #     GET_CONNECTION_STRING_REQUEST, self.handle_get_connection_string_request
        # )

    def shutdown(self) -> None:
        """Disconnect all connections when the service is shutting down"""
        if self._connection_manager is not None:
            self._connection_manager.close()

    # PUBLIC METHODS #######################################################
    def connect(self, params: ConnectRequestParams) -> Optional[ConnectionCompleteParams]:
        """
        Open a connection using the given connection information.

        If a connection was already open, disconnect first. Return a connection response
        indicating whether the connection was successful
        """
        owner_uri = params.owner_uri
        connection_details = params.connection
        if owner_uri is None:
            raise ValueError("No owner URI set")

        # Get the type of server and config
        config = self.service_provider.get(
            constants.WORKSPACE_SERVICE_NAME, WorkspaceService
        ).configuration

        try:
            if connection_details is None:
                raise ValueError("No connection details set")

            # Validate the connection details
            connection_details.validate_connection_params()

            connection_info = self._connection_manager.connect(
                owner_uri,
                connection_details,
                config,
            )
        except Exception as err:
            return _build_connection_response_error(owner_uri, err)

        self._notify_on_connect(connection_info)
        return connection_info.to_connection_complete_params()

    def disconnect(self, owner_uri: str) -> bool:
        """
        Closes all connections that belong to an owner URI
        :param owner_uri: URI of the connection to lookup and disconnect
        :return: True if the connections were found and disconnected disconnected,
            false otherwise
        """
        return self._connection_manager.disconnect(owner_uri)

    def get_connection(
        self, owner_uri: str, connection_type: ConnectionType | str
    ) -> Optional[ServerConnection]:
        """
        Get a connection for the given owner URI and connection type.

        NOTE: Use get_pooled_connection and use as a context manager instead of this method.
        If possible. This method will issue a long lived connection that cannot be
        shared.

        :raises ValueError: If there is no connection associated with the provided URI
        """
        if owner_uri is None:
            raise ValueError("No owner URI set")

        return self._connection_manager.get_long_lived_connection(owner_uri, connection_type)

    def get_pooled_connection(self, owner_uri: str) -> Optional[PooledConnection]:
        """
        Get a pooled connection for the given owner URI if it exists, otherwise return None
        """

        return self._connection_manager.get_pooled_connection(owner_uri)

    def register_on_connect_callback(
        self, task: Callable[[OwnerConnectionInfo], Any]
    ) -> None:
        self._on_connect_callbacks.append(task)

    def get_connection_info(self, owner_uri: str) -> OwnerConnectionInfo | None:
        """Get the ConnectionInfo object for the given owner URI,
        or None if there is no connection
        """
        return self._connection_manager.get_connection_info(owner_uri)

    # REQUEST HANDLERS #####################################################
    def handle_connect_request(
        self, request_context: RequestContext, params: ConnectRequestParams
    ) -> None:
        """Kick off a connection in response to an incoming connection request"""
        owner_uri = params.owner_uri
        if owner_uri is None:
            request_context.send_error("No owner URI set")
            return

        thread = threading.Thread(
            target=self._connect_and_respond, args=(request_context, params)
        )
        thread.daemon = True
        thread.start()

        request_context.send_response(True)

    def handle_disconnect_request(
        self, request_context: RequestContext, params: DisconnectRequestParams
    ) -> None:
        """Close a connection in response to an incoming disconnection request"""
        owner_uri = params.owner_uri
        if owner_uri is None:
            request_context.send_error("No owner URI set")
            return

        request_context.send_response(self.disconnect(owner_uri))

    def handle_list_databases(
        self,
        request_context: RequestContext,
        params: ListDatabasesParams,
    ) -> None:
        """List all databases on the server that the given URI has a connection to"""
        owner_uri = params.owner_uri
        if owner_uri is None:
            request_context.send_error("No owner URI set")
            return

        pooled_connection = self.get_pooled_connection(owner_uri)

        if pooled_connection is None:
            request_context.send_error("Connection could not be made.")
            return

        query_results = None
        try:
            with pooled_connection as connection:
                query_results = connection.list_databases()
        except Exception as err:
            self._log_exception(err)
            request_context.send_error(str(err))
            return

        database_names = [result[0] for result in query_results or []]
        request_context.send_response(ListDatabasesResponse(database_names=database_names))

    def handle_cancellation_request(
        self, request_context: RequestContext, params: CancelConnectParams
    ) -> None:
        """Cancel a connection attempt in response to a cancellation request"""
        owner_uri = params.owner_uri
        if owner_uri is None:
            request_context.send_error("No owner URI set")
            return

        # If the connection is being created, disconnecting will remove
        # the connection after the connection manager lock is released
        self._connection_manager.disconnect(owner_uri)
        request_context.send_response(True)  # VSCode doesn't use this response

    def handle_change_database_request(
        self, request_context: RequestContext, params: ChangeDatabaseRequestParams
    ) -> None:
        """change database of an existing connection or create a new connection
        with default database from input"""
        owner_uri = params.owner_uri
        if owner_uri is None:
            request_context.send_error("No owner URI set")
            return

        if params.new_database is None:
            request_context.send_error("No new database set")
            return

        connection_info: OwnerConnectionInfo | None = self.get_connection_info(owner_uri)

        if connection_info is None:
            return None

        connection_info_params: dict[str, str | int] = (
            connection_info.connection_details.options.copy()
        )
        connection_info_params["dbname"] = params.new_database
        connection_details: ConnectionDetails = ConnectionDetails.from_data(
            connection_info_params
        )

        connection_request_params: ConnectRequestParams = ConnectRequestParams(
            connection_details, params.owner_uri
        )
        self.handle_connect_request(request_context, connection_request_params)

    def handle_get_connection_string_request(
        self, request_context: RequestContext, params: GetConnectionStringParams
    ) -> None:
        raise NotImplementedError()

    # IMPLEMENTATION DETAILS ###############################################
    def _connect_and_respond(
        self, request_context: RequestContext, params: ConnectRequestParams
    ) -> None:
        """Open a connection and fire the connection complete notification"""
        response = self.connect(params)

        # Send the connection complete response unless the connection was canceled
        if response is not None:
            request_context.send_notification(CONNECTION_COMPLETE_METHOD, response)

    def _notify_on_connect(self, info: OwnerConnectionInfo) -> None:
        """
        Sends a notification to any listeners that a new connection has been established
        through a request from the client.
        """
        for callback in self._on_connect_callbacks:
            callback(info)

    def _fetch_azure_token(self, account_id: str, tenant_id: str | None) -> AzureToken:
        """Fetch an Azure token using the provided account and tenant IDs"""
        params = FetchAzureTokenRequestParams(
            account_id=account_id,
            tenant_id=tenant_id,
        )
        # Set timeout high, sometimes Azure token requests can take a while
        azure_token = self.server.send_request_sync(
            FETCH_AZURE_TOKEN_REQUEST_METHOD, params, AzureToken, timeout=20
        )
        if azure_token is None:
            raise AzureTokenRefreshError("Failed to fetch Azure token")
        return azure_token


def _build_connection_response_error(
    owner_uri: str, err: Exception
) -> ConnectionCompleteParams:
    """Build a connection complete response object"""

    # Add suggestions to error message. Will want to check for error code in the future.
    errorMessage = str(err)
    if "could not translate host name" in errorMessage:
        errorMessage += """\nCauses:
    Using the wrong hostname or problems with DNS resolution.\nSuggestions:
    Check that the server address or hostname is the full address."""

    if (
        "could not connect to server: Connection timed out" in errorMessage
        or "could not connect to server: Operation timed out" in errorMessage
    ):
        errorMessage += """\nSuggestions:
        Check that the firewall settings allow connections from the user's address."""

    return ConnectionCompleteParams.create_error(
        owner_uri=owner_uri,
        error_message=errorMessage,
    )
