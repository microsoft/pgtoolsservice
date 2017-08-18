# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing the disaster recovery service, including backup and restore functionality"""

import functools
import os
import subprocess
import sys

import inflection

from pgsqltoolsservice.capabilities.contracts import CategoryValue, FeatureMetadataProvider, ServiceOption
from pgsqltoolsservice.connection import ConnectionInfo
from pgsqltoolsservice.disaster_recovery.contracts.backup import BACKUP_REQUEST, BackupParams, BackupType
from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.tasks import Task, TaskResult, TaskStatus


class DisasterRecoveryService:
    """Manage backup and restore"""

    def __init__(self) -> None:
        self._service_provider: ServiceProvider = None

    def register(self, service_provider: ServiceProvider) -> None:
        """Register handlers with the service provider"""
        self._service_provider = service_provider

        # Register the handlers for the service
        self._service_provider.server.set_request_handler(BACKUP_REQUEST, self.handle_backup_request)

    def handle_backup_request(self, request_context: RequestContext, params: BackupParams) -> None:
        """
        Respond to disasterrecovery/backup requests by performing a backup

        :param request_context: The request context
        :param params: The BackupParams object for this request
        """
        connection_info: ConnectionInfo = self._service_provider[constants.CONNECTION_SERVICE_NAME].get_connection_info(params.owner_uri)
        if connection_info is None:
            request_context.send_error('No connection corresponding to the given owner URI')  # TODO: Localize
            return
        host = connection_info.details.options['host']
        database = connection_info.details.options['dbname']
        task = Task('Backup', f'Host: {host}, Database: {database}', constants.PROVIDER_NAME, host, database, request_context,  # TODO: Localize
                    functools.partial(_perform_backup, connection_info, params))
        request_context.send_response({})
        task.start()


def _perform_backup(connection_info: ConnectionInfo, params: BackupParams) -> TaskResult:
    """Call out to pg_dump to do a backup"""
    try:
        pg_dump_location = _get_pg_exe_path('pg_dump')
    except ValueError as e:
        return TaskResult(TaskStatus.FAILED, str(e))
    pg_dump_args = [pg_dump_location,
                    f'--file={params.backup_info.path}',
                    f'--format={_BACKUP_FORMAT_MAP[params.backup_info.type]}',
                    f'--dbname={connection_info.details.options["dbname"]}',
                    f'--host={connection_info.details.options["host"]}',
                    f'--username={connection_info.details.options["user"]}']
    # Add the rest of the options automatically
    for option, value in params.backup_info.__dict__.items():
        # If the option was already handled above, or is not set, then don't add it to the arguments
        if option == 'type' or option == 'path' or value is None or value is False:
            continue
        # Replace underscores with dashes in the option name
        key_name = inflection.dasherize(option)
        if value is True:
            # The option is a boolean flag, so just add the option
            pg_dump_args.append(f'--{key_name}')
        else:
            # The option has a value, so add the flag with its value
            pg_dump_args.append(f'--{key_name}={value}')

    pg_dump_process = subprocess.Popen(pg_dump_args, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    # pg_dump will prompt for the password, so send it via stdin. This call will block until the process exits.
    _, stderr = pg_dump_process.communicate(str.encode(connection_info.details.options.get('password') or ''))
    if pg_dump_process.returncode != 0:
        return TaskResult(TaskStatus.FAILED, str(stderr, 'utf-8'))
    return TaskResult(TaskStatus.SUCCEEDED)


def _get_pg_exe_path(exe_name: str) -> str:
    """
    Find the path to the given PostgreSQL utility executable for the current operating system

    :param exe_name: The name of the program to find (without .exe). e.g. 'pg_dump'
    :returns: The path to the requested executable
    :raises ValueError: if there is no file corresponding to the given exe_name
    """
    base_location = os.path.join(os.path.dirname(sys.argv[0]), 'pg_exes')
    platform = sys.platform
    if platform == 'win32':
        path = os.path.join(base_location, 'win', exe_name + '.exe')
    elif platform == 'darwin':
        path = os.path.join(base_location, 'mac', 'bin', exe_name)
    else:
        path = os.path.join(base_location, 'linux', 'bin', exe_name)

    # Verify that the file exists
    if not os.path.exists(path):
        raise ValueError(f'Could not find executable file {path}')  # TODO: Localize
    return path


# These options are handled in the _perform_backup method above. A few have special case handling, but most are handled automatically by using the option's
# name as the flag name, and the setting as the value. The BackupInfo contract has a field corresponding to each option.
# TODO: Localize the display names and descriptions
BACKUP_OPTIONS = FeatureMetadataProvider(
    True,
    'backup',
    [
        ServiceOption(
            name='type',
            display_name='Backup type',
            description='The type of backup to perform',
            value_type=ServiceOption.VALUE_TYPE_CATEGORY,
            is_required=True,
            category_values=[
                CategoryValue(
                    display_name='pg_dump/pg_restore (.dump)',
                    name='dump'
                ),
                CategoryValue(
                    display_name='Directory',
                    name='directory'
                ),
                CategoryValue(
                    display_name='Archive (.tar)',
                    name='tar'
                ),
                CategoryValue(
                    display_name='Plain text (.sql)',
                    name='sql'
                ),
            ],
            default_value='sql'
        ),
        ServiceOption(
            name='path',
            display_name='Output path',
            description='The path to the backup file/directory that will be produced',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=True
        ),
        ServiceOption(
            name='jobs',
            display_name='Number of jobs',
            description='The number of parallel jobs to use for the dump',
            value_type=ServiceOption.VALUE_TYPE_NUMBER,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='compress',
            display_name='Compression level',
            description='The compression level (for compressed formats)',
            value_type=ServiceOption.VALUE_TYPE_CATEGORY,
            is_required=False,
            group_name='Advanced',
            category_values=[CategoryValue('0', '0'), CategoryValue('1', '1'), CategoryValue('2', '2'), CategoryValue('3', '3'), CategoryValue('4', '4'),
                             CategoryValue('5', '5'), CategoryValue('6', '6'), CategoryValue('7', '7'), CategoryValue('8', '8'), CategoryValue('9', '9')]
        ),
        ServiceOption(
            name='dataOnly',
            display_name='Data only',
            description='Dump only the data, not the schema',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='blobs',
            display_name='Blobs',
            description='Include large objects in dump',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='clean',
            display_name='Clean',
            description='Clean (drop) database objects before recreating',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='create',
            display_name='Create',
            description='Include commands to create database in dump',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='encoding',
            display_name='Encoding',
            description='Dump the data in the given encoding',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='schema',
            display_name='Schema',
            description='Dump the named schema(s) only',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='excludeSchema',
            display_name='Exclude schema',
            description='Do not dump the named schema(s)',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='oids',
            display_name='OIDs',
            description='Include OIDs in the dump',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='noOwner',
            display_name='No owner',
            description='Skip restoration of object ownership in plain-text format',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='schemaOnly',
            display_name='Schema only',
            description='Dump only the schema, no data',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='superuser',
            display_name='Superuser',
            description='Superuser user name to use in plain-text format',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='table',
            display_name='Table',
            description='Dump the named table(s) only',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='excludeTable',
            display_name='Exclude table',
            description='Do not dump the named table(s)',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='noPrivileges',
            display_name='No privileges',
            description='Do not dump privileges (grant/revoke)',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='columnInserts',
            display_name='Column inserts',
            description='Dump data as INSERT commands with column names',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='disableDollarQuoting',
            display_name='Disable dollar quoting',
            description='Disable dollar quoting; use SQL standard quoting',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='disableTriggers',
            display_name='Disable triggers',
            description='Disable triggers during data-only restore',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='enable_row_security',
            display_name='Enable row security',
            description='Dump only content user has access to',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='excludeDataTable',
            display_name='Exclude data table',
            description='Do not dump data for the named table(s)',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='ifExists',
            display_name='Use IF EXISTS',
            description='Use IF EXISTS when dropping objects',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='inserts',
            display_name='Inserts',
            description='Dump data as INSERT commands, rather than COPY',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='noSecurityLabels',
            display_name='No security labels',
            description='Do not dump security label assignments',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='noSynchronizedSnapshots',
            display_name='No synchronized snapshots',
            description='Do not use synchronized snapshots in parallel jobs',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='noTablespaces',
            display_name='No tablespaces',
            description='Do not dump tablespace assignments',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='noUnloggedTableData',
            display_name='No unlogged table data',
            description='Do not dump unlogged table data',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='quoteAllIidentifiers',
            display_name='Quote all identifiers',
            description='Quote all identifiers, even if not key words',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='section',
            display_name='Section',
            description='Dump named section (pre-data, data, or post-data)',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='serializableDeferrable',
            display_name='Serializable deferrable',
            description='Wait until the dump can run without anomalies',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='snapshot',
            display_name='Snapshot',
            description='Use given snapshot for the dump',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='strictNames',
            display_name='Strict names',
            description='Require table and/or schema include patterns to match at least one entity each',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='useSetSessionAuthorization',
            display_name='Use SET SESSION AUTHORIZATION',
            description='Use SET SESSION AUTHORIZATION commands instead of ALTER OWNER commands to set ownership',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        )])


# Map from backup types to the corresponding pg_dump format option value
_BACKUP_FORMAT_MAP = {
    BackupType.DIRECTORY: 'd',
    BackupType.PG_DUMP: 'c',
    BackupType.PLAIN_TEXT: 'p',
    BackupType.TAR: 't'
}
