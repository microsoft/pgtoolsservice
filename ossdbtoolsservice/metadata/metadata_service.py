# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading

from ossdbtoolsservice.connection.connection_service import ConnectionService
from ossdbtoolsservice.hosting import RequestContext, Service, ServiceProvider
from ossdbtoolsservice.metadata.contracts import (
    METADATA_LIST_REQUEST,
    MetadataListParameters,
    MetadataListResponse,
    MetadataType,
    ObjectMetadata,
)
from ossdbtoolsservice.utils import constants

# This query collects all the tables, views,
# and functions in all the schemas in the database(s)?
PG_METADATA_QUERY = """
SELECT s.nspname AS schema_name, 
    p.proname || '(' || COALESCE(pg_catalog.pg_get_function_identity_arguments(p.oid), 
        '') || ')' AS object_name, \
    'f' as type FROM pg_proc p
    INNER JOIN pg_namespace s ON s.oid = p.pronamespace
    WHERE s.nspname NOT ILIKE 'pg_%' AND s.nspname != 'information_schema'
UNION
SELECT schemaname AS schema_name, tablename AS object_name, 't' as type FROM pg_tables
    WHERE schemaname NOT ILIKE 'pg_%' AND schemaname != 'information_schema'
      AND tablename NOT IN ( SELECT relname FROM pg_class WHERE relispartition )
UNION
SELECT schemaname AS schema_name, viewname AS object_name, 'v' as type from pg_views
    WHERE schemaname NOT ILIKE 'pg_%' AND schemaname != 'information_schema'
"""


class MetadataService(Service):
    """Service for database metadata support"""

    def register(self, service_provider: ServiceProvider) -> None:
        self._service_provider = service_provider

        # Register the request handlers with the server
        self._service_provider.server.set_request_handler(
            METADATA_LIST_REQUEST, self._handle_metadata_list_request
        )

        if self._service_provider.logger is not None:
            self._service_provider.logger.info("Metadata service successfully initialized")

    # REQUEST HANDLERS #####################################################

    def _handle_metadata_list_request(
        self, request_context: RequestContext, params: MetadataListParameters
    ) -> None:
        thread = threading.Thread(
            target=self._metadata_list_worker, args=(request_context, params)
        )
        thread.daemon = True
        thread.start()

    def _metadata_list_worker(
        self, request_context: RequestContext, params: MetadataListParameters
    ) -> None:
        try:
            owner_uri = params.owner_uri
            if owner_uri is None:
                raise Exception("Owner URI is required")
            metadata = self._list_metadata(owner_uri)
            request_context.send_response(MetadataListResponse(metadata))
        except Exception as e:
            self._log_exception(e)
            request_context.send_error(
                "Error while listing metadata: " + str(e)
            )  # TODO: Localize

    def _list_metadata(self, owner_uri: str) -> list[ObjectMetadata]:
        # Get current connection
        connection_service = self.service_provider.get(
            constants.CONNECTION_SERVICE_NAME, ConnectionService
        )
        pooled_connection = connection_service.get_pooled_connection(owner_uri)

        if pooled_connection is None:
            raise Exception("Connection is required")

        with pooled_connection as connection:
            # Get the current database
            database_name = connection.database_name

            # Get the metadata query specific to the current provider
            # and fill in the database name
            metadata_query = PG_METADATA_QUERY.format(database_name)

            query_results = connection.execute_query(metadata_query, all=True)

        metadata_list = []
        if query_results:
            for row in query_results:
                schema_name = row[0]
                object_name = row[1]
                object_type = _METADATA_TYPE_MAP[row[2]]
                metadata_list.append(
                    ObjectMetadata(None, object_type, None, object_name, schema_name)
                )
        return metadata_list


_METADATA_TYPE_MAP = {
    "f": MetadataType.FUNCTION,
    "t": MetadataType.TABLE,
    "v": MetadataType.VIEW,
    "s": MetadataType.SPROC,
}
