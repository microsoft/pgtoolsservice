# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing the disaster recovery service, including backup and restore functionality"""

import functools
import os
import subprocess
import sys

from pgsqltoolsservice.connection import ConnectionInfo
from pgsqltoolsservice.disaster_recovery.contracts.backup import BACKUP_CONFIG_INFO_REQUEST, BACKUP_REQUEST, BackupParams, DefaultDatabaseInfoParams
from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.tasks import Task


class DisasterRecoveryService:
    """Manage backup and restore"""

    def __init__(self) -> None:
        self._service_provider: ServiceProvider = None

    def register(self, service_provider: ServiceProvider) -> None:
        """Register handlers with the service provider"""
        self._service_provider = service_provider

        # Register the handlers for the service
        self._service_provider.server.set_request_handler(BACKUP_CONFIG_INFO_REQUEST, handle_backup_config_info_request)
        self._service_provider.server.set_request_handler(BACKUP_REQUEST, self.handle_backup_request)

    def handle_backup_request(self, request_context: RequestContext, params: BackupParams) -> None:
        """Respond to disasterrecovery/backup requests by performing a backup"""
        connection_info: ConnectionInfo = self._service_provider[constants.CONNECTION_SERVICE_NAME].owner_to_connection_map[params.owner_uri]
        host = connection_info.details.options['host']
        database = connection_info.details.options['dbname']
        task = Task('Backup', f'Host: {host}, Database: {database}', constants.PROVIDER_NAME, host, database, request_context,  # TODO: Localize
                    functools.partial(perform_backup, connection_info, params))
        request_context.send_response({})
        task.start()


def perform_backup(connection_info: ConnectionInfo, params: BackupParams) -> None:
    """Call out to pg_dump to do a backup"""
    pg_dump_location = _get_pg_exe_path('pg_dump')
    pg_dump_args = [pg_dump_location,
                    f'--file={params.backup_info.backup_path_list[0]}',
                    '--format=p',
                    f'--dbname={connection_info.details.options["dbname"]}',
                    f'--host={connection_info.details.options["host"]}',
                    f'--username={connection_info.details.options["user"]}']
    pg_dump_process = subprocess.Popen(pg_dump_args, stdin=subprocess.PIPE)
    # pg_dump will prompt for the password, so send it via stdin. This call will block until the process exits.
    pg_dump_process.communicate(str.encode(connection_info.details.options.get('password') or ''))


def handle_backup_config_info_request(request_context: RequestContext, _: DefaultDatabaseInfoParams) -> None:
    """Respond to disasterrecovery/backupconfiginfo requests by giving information about the database"""
    # Send a hardcoded response for now since Postgres does not care about any of these options
    request_context.send_response(
        {'backupConfigInfo': {'lastBackupLocations': [], 'defaultNewBackupFolder': '', 'recoveryModel': 'Simple', 'backupEncryptors': []}})


def _get_pg_exe_path(exe_name: str) -> str:
    """
    Find the path to the given PostgreSQL utility executable for the current operating system

    :param exe_name: The name of the program to find (without .exe). e.g. 'pg_dump'
    :returns: The path to the requested executable
    """
    base_location = os.path.join(os.path.dirname(sys.argv[0]), 'pg_exes')
    platform = sys.platform
    if platform == 'win32':
        return os.path.join(base_location, 'win', exe_name + '.exe')
    elif platform == 'darwin':
        return os.path.join(base_location, 'mac', 'bin', exe_name)
    else:
        return os.path.join(base_location, 'linux', 'bin', exe_name)
