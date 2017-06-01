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
                    name='connectionString',
                    displayName='Connection String',
                    description='PostgreSQL-format connection string',
                    valueType=ConnectionOption.VALUE_TYPE_STRING,
                    isIdentity=True,
                    isRequired=False,
                    groupName='Source'
                ),
                ConnectionOption(
                    name='server',
                    displayName='Server Name',
                    description='Name of the PostgreSQL instance',
                    valueType=ConnectionOption.VALUE_TYPE_STRING,
                    specialValueType=ConnectionOption.SPECIAL_VALUE_SERVER_NAME,
                    isIdentity=True,
                    isRequired=True,
                    groupName='Source'
                ),
                ConnectionOption(
                    name='database',
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
                    name='authenticationType',
                    displayName='Authentication Type',
                    description='Specifies the method of authenticating with SQL Server',
                    valueType=ConnectionOption.VALUE_TYPE_CATEGORY,
                    specialValueType=ConnectionOption.SPECIAL_VALUE_AUTH_TYPE,
                    isIdentity=True,
                    isRequired=True,
                    groupName='Security',
                    categoryValues=[
                        CategoryValue('SQL Login', 'SqlLogin')
                    ]
                )
            ])
        ))
        # Since jsonrpc expects a serializable object, convert it to a dictionary
        return utils.object_to_dictionary(server_capabilities)

