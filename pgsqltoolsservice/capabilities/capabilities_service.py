# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from pgsqltoolsservice.capabilities.contracts import (
    CAPABILITIES_REQUEST,
    CapabilitiesRequestParams,
    CapabilitiesResult, DMPServerCapabilities, ConnectionProviderOptions, CategoryValue, ConnectionOption,
    INITIALIZE_REQUEST,
    InitializeRequestParams,
    InitializeResult, ServerCapabilities, TextDocumentSyncKind
)
from pgsqltoolsservice.hosting import RequestContext, ServiceProvider


class CapabilitiesService:

    def __init__(self):
        self._service_provider: ServiceProvider = None

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider

        self._service_provider.server.set_request_handler(CAPABILITIES_REQUEST, self._handle_dmp_capabilities_request)
        self._service_provider.server.set_request_handler(INITIALIZE_REQUEST, self._handle_initialize_request)

    @staticmethod
    def _handle_dmp_capabilities_request(
            request_context: RequestContext,
            params: [CapabilitiesRequestParams, None]
    ) -> None:
        """
        Sends the capabilities of the tools service data protocol features
        :param request_context: Context of the request
        :param params: Parameters for the capabilities request
        """
        result = CapabilitiesResult()
        result.capabilities = DMPServerCapabilities()
        result.capabilities.protocol_version = '1.0'
        result.capabilities.provider_name = 'PGSQL'
        result.capabilities.provider_display_name = 'PostgreSQL'
        result.capabilities.connection_provider = ConnectionProviderOptions([
            ConnectionOption(
                name='host',
                display_name='Server Name',
                description='Name of the PostgreSQL instance',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                special_value_type=ConnectionOption.SPECIAL_VALUE_SERVER_NAME,
                is_identity=True,
                is_required=True,
                group_name='Source'
            ),
            ConnectionOption(
                name='dbname',
                display_name='Database Name',
                description='The name of the initial catalog or database in the data source',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                special_value_type=ConnectionOption.SPECIAL_VALUE_DATABASE_NAME,
                is_identity=True,
                is_required=False,
                group_name='Source'
            ),
            ConnectionOption(
                name='user',
                display_name='User Name',
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
                display_name='Host IP Address',
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
                display_name='Connect Timeout',
                description='Seconds to wait before timing out when connecting',
                value_type=ConnectionOption.VALUE_TYPE_NUMBER,
                group_name='Client',
                default_value='15'
            ),
            ConnectionOption(
                name='clientEncoding',
                display_name='Client Encoding',
                description='The client encoding for the connection',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='Client'
            ),
            ConnectionOption(
                name='options',
                display_name='Command-Line Options',
                description='Command-line options to send to the server when the connection starts',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='Server'
            ),
            ConnectionOption(
                name='applicationName',
                display_name='Application Name',
                description='Value for the "application_name" configuration parameter',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='Client',
                special_value_type=ConnectionOption.SPECIAL_VALUE_APP_NAME
            ),
            ConnectionOption(
                name='sslmode',
                display_name='SSL Mode',
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
                ]
            ),
            ConnectionOption(
                name='sslcompression',
                display_name='Use SSL Compression',
                description='Whether to compress SSL connections',
                value_type=ConnectionOption.VALUE_TYPE_BOOLEAN,
                group_name='SSL'
            ),
            ConnectionOption(
                name='sslcert',
                display_name='SSL Certificate Filename',
                description='The filename of the SSL certificate to use',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='SSL'
            ),
            ConnectionOption(
                name='sslkey',
                display_name='SSL Key Filename',
                description='The filename of the key to use for the SSL certificate',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='SSL'
            ),
            ConnectionOption(
                name='sslrootcert',
                display_name='SSL Root Certificate Filename',
                description='The filename of the SSL root CA certificate to use',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='SSL'
            ),
            ConnectionOption(
                name='sslcrl',
                display_name='SSL CRL Filename',
                description='The filename of the SSL certificate revocation list to use',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='SSL'
            ),
            ConnectionOption(
                name='requirepeer',
                display_name='Require Peer',
                description='The required username of the server process',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='Server'
            ),
            ConnectionOption(
                name='service',
                display_name='Service Name',
                description='The service name in pg_service.conf to use for connection parameters',
                value_type=ConnectionOption.VALUE_TYPE_STRING,
                group_name='Client'
            )
        ])

        # Send the response
        request_context.send_response(result)

    @staticmethod
    def _handle_initialize_request(request_context: RequestContext, params: [InitializeRequestParams, None]) -> None:
        """
        Sends the capabilities of the tools service language features
        :param request_context: Context for the request
        :param params: Initialization request parameters
        """
        result = InitializeResult()
        result.capabilities = ServerCapabilities(
            text_document_sync=TextDocumentSyncKind.INCREMENTAL,
            definition_provider=False,
            references_provider=False,
            document_formatting_provider=False,
            document_range_formatting_provider=False,
            document_highlight_provider=False,
            hover_provider=False,
            completion_provider=None
        )

        # Send the request
        request_context.send_response(result)
