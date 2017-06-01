# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from pgsqltoolsservice import utils
from pgsqltoolsservice.capabilities.contracts.capabilities_request import CapabilitiesResult
from pgsqltoolsservice.capabilities.contracts.connection_provider_options import (
    CategoryValue,
    ConnectionOption,
    ConnectionProviderOptions
)
from pgsqltoolsservice.capabilities.contracts.dmp_server_capabilities import DMPServerCapabilities


class CapabilitiesService:

    def __init__(self):
        pass

    @staticmethod
    def handle_db_capabilities_request(hostName, hostVersion):
        """Get the server capabilities response"""
        server_capabilities = CapabilitiesResult(DMPServerCapabilities(
            protocolVersion='1.0',
            providerName='PGSQL',
            providerDisplayName='PostgreSQL',
            connectionProvider=ConnectionProviderOptions(options=[
                ConnectionOption(
                    name='host',
                    displayName='Server Name',
                    description='Name of the PostgreSQL instance',
                    valueType=ConnectionOption.VALUE_TYPE_STRING,
                    specialValueType=ConnectionOption.SPECIAL_VALUE_SERVER_NAME,
                    isIdentity=True,
                    isRequired=True,
                    groupName='Source'
                ),
                ConnectionOption(
                    name='dbname',
                    displayName='Database Name',
                    description='The name of the initial catalog or database in the data source',
                    valueType=ConnectionOption.VALUE_TYPE_STRING,
                    specialValueType=ConnectionOption.SPECIAL_VALUE_DATABASE_NAME,
                    isIdentity=True,
                    isRequired=False,
                    groupName='Source'
                ),
                ConnectionOption(
                    name='user',
                    displayName='User Name',
                    description='Indicates the user ID to be used when connecting to the data source',
                    valueType=ConnectionOption.VALUE_TYPE_STRING,
                    specialValueType=ConnectionOption.SPECIAL_VALUE_USER_NAME,
                    isIdentity=True,
                    isRequired=True,
                    groupName='Security'
                ),
                ConnectionOption(
                    name='password',
                    displayName='Password',
                    description='Indicates the password to be used when connecting to the data source',
                    valueType=ConnectionOption.VALUE_TYPE_PASSWORD,
                    specialValueType=ConnectionOption.SPECIAL_VALUE_PASSWORD_NAME,
                    isIdentity=True,
                    isRequired=True,
                    groupName='Security'
                ),
                ConnectionOption(
                    name='hostaddr',
                    displayName='Host IP Address',
                    description='IP address of the server',
                    valueType=ConnectionOption.VALUE_TYPE_STRING,
                    groupName='Server'
                ),
                ConnectionOption(
                    name='port',
                    displayName='Port',
                    description='Port number for the server',
                    valueType=ConnectionOption.VALUE_TYPE_STRING,
                    groupName='Server'
                ),
                ConnectionOption(
                    name='connectTimeout',
                    displayName='Connect Timeout',
                    description='Seconds to wait before timing out when connecting',
                    valueType=ConnectionOption.VALUE_TYPE_NUMBER,
                    groupName='Client',
                    defaultValue=15
                ),
                ConnectionOption(
                    name='clientEncoding',
                    displayName='Client Encoding',
                    description='The client encoding for the connection',
                    valueType=ConnectionOption.VALUE_TYPE_STRING,
                    groupName='Client'
                ),
                ConnectionOption(
                    name='options',
                    displayName='Command-Line Options',
                    description='Command-line options to send to the server when the connection starts',
                    valueType=ConnectionOption.VALUE_TYPE_STRING,
                    groupName='Server'
                ),
                ConnectionOption(
                    name='applicationName',
                    displayName='Application Name',
                    description='Value for the "application_name" configuration parameter',
                    valueType=ConnectionOption.VALUE_TYPE_STRING,
                    groupName='Client',
                    specialValueType=ConnectionOption.SPECIAL_VALUE_APP_NAME
                ),
                ConnectionOption(
                    name='sslmode',
                    displayName='SSL Mode',
                    description='The SSL mode to use when connecting',
                    valueType=ConnectionOption.VALUE_TYPE_CATEGORY,
                    groupName='SSL',
                    categoryValues=[
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
                    displayName='Use SSL Compression',
                    description='Whether to compress SSL connections',
                    valueType=ConnectionOption.VALUE_TYPE_BOOLEAN,
                    groupName='SSL'
                ),
                ConnectionOption(
                    name='sslcert',
                    displayName='SSL Certificate Filename',
                    description='The filename of the SSL certificate to use',
                    valueType=ConnectionOption.VALUE_TYPE_STRING,
                    groupName='SSL'
                ),
                ConnectionOption(
                    name='sslkey',
                    displayName='SSL Key Filename',
                    description='The filename of the key to use for the SSL certificate',
                    valueType=ConnectionOption.VALUE_TYPE_STRING,
                    groupName='SSL'
                ),
                ConnectionOption(
                    name='sslrootcert',
                    displayName='SSL Root Certificate Filename',
                    description='The filename of the SSL root CA certificate to use',
                    valueType=ConnectionOption.VALUE_TYPE_STRING,
                    groupName='SSL'
                ),
                ConnectionOption(
                    name='sslcrl',
                    displayName='SSL CRL Filename',
                    description='The filename of the SSL certificate revocation list to use',
                    valueType=ConnectionOption.VALUE_TYPE_STRING,
                    groupName='SSL'
                ),
                ConnectionOption(
                    name='requirepeer',
                    displayName='Require Peer',
                    description='The required username of the server process',
                    valueType=ConnectionOption.VALUE_TYPE_STRING,
                    groupName='Server'
                ),
                ConnectionOption(
                    name='service',
                    displayName='Service Name',
                    description='The service name in pg_service.conf to use for connection parameters',
                    valueType=ConnectionOption.VALUE_TYPE_STRING,
                    groupName='Client'
                )
            ])
        ))
        # Since jsonrpc expects a serializable object, convert it to a dictionary
        return utils.object_to_dictionary(server_capabilities)
