# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

from pgsqltoolsservice.capabilities.contracts import (
    CAPABILITIES_REQUEST,
    CapabilitiesRequestParams, CompletionOptions,
    CapabilitiesResult, DMPServerCapabilities, ConnectionProviderOptions, CategoryValue, ConnectionOption,
    INITIALIZE_REQUEST,
    InitializeRequestParams,
    InitializeResult, ServerCapabilities, TextDocumentSyncKind
)
from pgsqltoolsservice.disaster_recovery import BACKUP_OPTIONS
from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.utils import constants


class CapabilitiesService:
    """Defines the capabilities supported by PG Tools including language service and DMP support"""

    def __init__(self):
        self._service_provider: ServiceProvider = None

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider

        self._service_provider.server.set_request_handler(CAPABILITIES_REQUEST, self._handle_dmp_capabilities_request)
        self._service_provider.server.set_request_handler(INITIALIZE_REQUEST, self._handle_initialize_request)

    def _handle_dmp_capabilities_request(
            self,
            request_context: RequestContext,
            params: Optional[CapabilitiesRequestParams]
    ) -> None:
        """
        Sends the capabilities of the tools service data protocol features
        :param request_context: Context of the request
        :param params: Parameters for the capabilities request
        """
        workspace_service = self._service_provider[constants.WORKSPACE_SERVICE_NAME]
        conn_provider_opts = ConnectionProviderOptions([
            ConnectionOption(
                name='host',
                display_name='Server name',
                description='Name of the PostgreSQL instance',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                special_value_type=ConnectionOption.SPECIAL_VALUE_SERVER_NAME,
                is_identity=True,
                is_required=True,
                group_name='Source'
            ),
            ConnectionOption(
                name='dbname',
                display_name='Database name',
                description='The name of the initial catalog or database in the data source',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                special_value_type=ConnectionOption.SPECIAL_VALUE_DATABASE_NAME,
                is_identity=True,
                is_required=False,
                group_name='Source',
                default_value=workspace_service.configuration.pgsql.default_database
            ),
            ConnectionOption(
                name='user',
                display_name='User name',
                description='Indicates the user ID to be used when connecting to the data source',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                special_value_type=ConnectionOption.SPECIAL_VALUE_USER_NAME,
                is_identity=True,
                is_required=True,
                group_name='Security'
            ),
            ConnectionOption(
                name='password',
                display_name='Password',
                description='Indicates the password to be used when connecting to the data source',
                value_type=ConnectionOption.VALUE_TYPE_PASSWORD,
                special_value_type=ConnectionOption.SPECIAL_VALUE_PASSWORD_NAME,
                is_identity=True,
                is_required=True,
                group_name='Security'
            ),
            ConnectionOption(
                name='hostaddr',
                display_name='Host IP address',
                description='IP address of the server',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='Server'
            ),
            ConnectionOption(
                name='port',
                display_name='Port',
                description='Port number for the server',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='Server'
            ),
            ConnectionOption(
                name='connectTimeout',
                display_name='Connect timeout',
                description='Seconds to wait before timing out when connecting',
                value_type=ConnectionOption.VALUE_TYPE_NUMBER,
                group_name='Client',
                default_value='15'
            ),
            ConnectionOption(
                name='clientEncoding',
                display_name='Client encoding',
                description='The client encoding for the connection',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='Client'
            ),
            ConnectionOption(
                name='options',
                display_name='Command-line options',
                description='Command-line options to send to the server when the connection starts',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='Server'
            ),
            ConnectionOption(
                name='applicationName',
                display_name='Application name',
                description='Value for the "application_name" configuration parameter',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='Client',
                special_value_type=ConnectionOption.SPECIAL_VALUE_APP_NAME
            ),
            ConnectionOption(
                name='sslmode',
                display_name='SSL mode',
                description='The SSL mode to use when connecting',
                value_type=ConnectionOption.VALUE_TYPE_CATEGORY,
                group_name='SSL',
                category_values=[
                    CategoryValue('Disable', 'disable'),
                    CategoryValue('Allow', 'allow'),
                    CategoryValue('Prefer', 'prefer'),
                    CategoryValue('Require', 'require'),
                    CategoryValue('Verify-CA', 'verify-ca'),
                    CategoryValue('Verify-Full', 'verify-full'),
                ],
                default_value='prefer'
            ),
            ConnectionOption(
                name='sslcompression',
                display_name='Use SSL compression',
                description='Whether to compress SSL connections',
                value_type=ConnectionOption.VALUE_TYPE_BOOLEAN,
                group_name='SSL'
            ),
            ConnectionOption(
                name='sslcert',
                display_name='SSL certificate filename',
                description='The filename of the SSL certificate to use',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='SSL'
            ),
            ConnectionOption(
                name='sslkey',
                display_name='SSL key filename',
                description='The filename of the key to use for the SSL certificate',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='SSL'
            ),
            ConnectionOption(
                name='sslrootcert',
                display_name='SSL root certificate filename',
                description='The filename of the SSL root CA certificate to use',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='SSL'
            ),
            ConnectionOption(
                name='sslcrl',
                display_name='SSL CRL filename',
                description='The filename of the SSL certificate revocation list to use',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='SSL'
            ),
            ConnectionOption(
                name='requirepeer',
                display_name='Require peer',
                description='The required username of the server process',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='Server'
            ),
            ConnectionOption(
                name='service',
                display_name='Service name',
                description='The service name in pg_service.conf to use for connection parameters',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='Client'
            )
        ])
        capabilities = DMPServerCapabilities('1.0', 'PGSQL', 'PostgreSQL', conn_provider_opts, [BACKUP_OPTIONS])
        result = CapabilitiesResult(capabilities)

        # Send the response
        request_context.send_response(result)

    @staticmethod
    def _handle_initialize_request(request_context: RequestContext, params: Optional[InitializeRequestParams]) -> None:
        """
        Sends the capabilities of the tools service language features
        :param request_context: Context for the request
        :param params: Initialization request parameters
        """
        capabilities = ServerCapabilities(
            text_document_sync=TextDocumentSyncKind.INCREMENTAL,
            definition_provider=False,
            references_provider=False,
            document_formatting_provider=False,
            document_range_formatting_provider=False,
            document_highlight_provider=False,
            hover_provider=False,
            completion_provider=CompletionOptions(True, ['.', '-', ':', '\\', '[', '"'])
        )
        result = InitializeResult(capabilities)

        # Send the request
        request_context.send_response(result)
