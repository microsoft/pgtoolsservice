# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading
from typing import List

from ossdbtoolsservice.driver import ServerConnection
from ossdbtoolsservice.connection.contracts import ConnectionType
from ossdbtoolsservice.hosting import RequestContext, ServiceProvider
from ossdbtoolsservice.metadata.contracts import (
    MetadataListParameters, MetadataListResponse, METADATA_LIST_REQUEST, MetadataType, ObjectMetadata)
from ossdbtoolsservice.utils import constants

# This query collects all the tables, views, and functions in all the schemas in the database(s)?
PG_METADATA_QUERY = """
SELECT s.nspname AS schema_name, p.proname || '(' || COALESCE(pg_catalog.pg_get_function_identity_arguments(p.oid), '') || ')' AS object_name, \
    'f' as type FROM pg_proc p
    INNER JOIN pg_namespace s ON s.oid = p.pronamespace
    WHERE s.nspname NOT ILIKE 'pg_%' AND s.nspname != 'information_schema'
UNION
SELECT schemaname AS schema_name, tablename AS object_name, 't' as type FROM pg_tables
    WHERE schemaname NOT ILIKE 'pg_%' AND schemaname != 'information_schema'
UNION
SELECT schemaname AS schema_name, viewname AS object_name, 'v' as type from pg_views
    WHERE schemaname NOT ILIKE 'pg_%' AND schemaname != 'information_schema'
"""

QUERY_MAP = {
    constants.PG_PROVIDER_NAME: PG_METADATA_QUERY
}


class MetadataService:
    """Service for database metadata support"""

    def __init__(self):
        self._service_provider: ServiceProvider = None

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider

        # Register the request handlers with the server
        self._service_provider.server.set_request_handler(
            METADATA_LIST_REQUEST, self._handle_metadata_list_request
        )

        if self._service_provider.logger is not None:
            self._service_provider.logger.info('Metadata service successfully initialized')

    # REQUEST HANDLERS #####################################################

    def _handle_metadata_list_request(self, request_context: RequestContext, params: MetadataListParameters) -> None:
        thread = threading.Thread(
            target=self._metadata_list_worker,
            args=(request_context, params)
        )
        thread.daemon = True
        thread.start()

    def _metadata_list_worker(self, request_context: RequestContext, params: MetadataListParameters) -> None:
        try:
            metadata = self._list_metadata(params.owner_uri)
            request_context.send_response(MetadataListResponse(metadata))
        except Exception as e:
            if self._service_provider.logger is not None:
                self._service_provider.logger.exception('Unhandled exception while executing the metadata list worker thread')
            request_context.send_error('Unhandled exception while listing metadata: ' + str(e))  # TODO: Localize

    def _list_metadata(self, owner_uri: str) -> List[ObjectMetadata]:
        # Get current connection
        connection_service = self._service_provider[constants.CONNECTION_SERVICE_NAME]
        connection: ServerConnection = connection_service.get_connection(owner_uri, ConnectionType.DEFAULT)

        # Get the current database
        database_name = connection.database_name

        # Get the metadata query specific to the current provider and fill in the database name
        metadata_query = QUERY_MAP[self._service_provider.provider].format(database_name)

        query_results = connection.execute_query(metadata_query, all=True)

        metadata_list = []
        if query_results:
            for row in query_results:
                schema_name = row[0]
                object_name = row[1]
                object_type = _METADATA_TYPE_MAP[row[2]]
                metadata_list.append(ObjectMetadata(None, object_type, None, object_name, schema_name))
        return metadata_list


_METADATA_TYPE_MAP = {
    'f': MetadataType.FUNCTION,
    't': MetadataType.TABLE,
    'v': MetadataType.VIEW,
    's': MetadataType.SPROC
}
