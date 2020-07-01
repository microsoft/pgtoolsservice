# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.capabilities.contracts import (
    DMPServerCapabilities, ConnectionProviderOptions, CategoryValue, ConnectionOption
)
from ossdbtoolsservice.disaster_recovery.contracts import BACKUP_OPTIONS, RESTORE_OPTIONS
from ossdbtoolsservice.query_execution.contracts import SERIALIZATION_OPTIONS
from ossdbtoolsservice.utils import constants

mysql_conn_provider_opts = ConnectionProviderOptions([
    ConnectionOption(
        name='host',
        display_name='Server name',
        description='Name of the MySQL instance',
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
        default_value=constants.DEFAULT_DB[constants.MYSQL_PROVIDER_NAME]
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
        name='bindAddress',
        display_name='Host IP address',
        description='IP address of the server',
        value_type=ConnectionOption.VALUE_TYPE_STRING,
        group_name='Server'
    ),
    ConnectionOption(
        name='port',
        display_name='Port',
        description='Port number for the server',
        value_type=ConnectionOption.VALUE_TYPE_NUMBER,
        group_name='Server'
    ),
    ConnectionOption(
        name='connectTimeout',
        display_name='Connect timeout',
        description='Seconds to wait before timing out when connecting',
        value_type=ConnectionOption.VALUE_TYPE_NUMBER,
        group_name='Client',
        default_value='10'
    ),
    ConnectionOption(
        name='readTimeout',
        display_name='Read timeout',
        description='Seconds to wait when reading from the connection',
        value_type=ConnectionOption.VALUE_TYPE_NUMBER,
        group_name='Client',
        default_value=''
    ),
    ConnectionOption(
        name='writeTimeout',
        display_name='Write timeout',
        description='Seconds to wait when writing to the connection',
        value_type=ConnectionOption.VALUE_TYPE_NUMBER,
        group_name='Client',
        default_value=''
    ),
    ConnectionOption(
        name='clientFlag',
        display_name='Capability flags',
        description='Custom flags to send to the MySQL server',
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
        name='ssl',
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
        default_value='allow'
    ),
    ConnectionOption(
        name='ssl.cert',
        display_name='SSL certificate filename',
        description='The filename of the SSL certificate to use',
        value_type=ConnectionOption.VALUE_TYPE_STRING,
        group_name='SSL'
    ),
    ConnectionOption(
        name='ssl.key',
        display_name='SSL key filename',
        description='The filename of the key to use for the SSL certificate',
        value_type=ConnectionOption.VALUE_TYPE_STRING,
        group_name='SSL'
    ),
    ConnectionOption(
        name='ssl.ca',
        display_name='SSL root certificate filename',
        description='The path name of the SSL root CA certificate',
        value_type=ConnectionOption.VALUE_TYPE_STRING,
        group_name='SSL'
    ),
    ConnectionOption(
        name='ssl.cipher',
        display_name='SSL cipher',
        description='Comma-seperated list of allowed ciphers for SSL encryption',
        value_type=ConnectionOption.VALUE_TYPE_STRING,
        group_name='SSL'
    )
])

capabilities = DMPServerCapabilities('1.0', 'MySQL', 'MySQL', mysql_conn_provider_opts, [SERIALIZATION_OPTIONS])