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
from pgsqltoolsservice.tasks import Task, TaskResult, TaskStatus


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
                    f'--file={params.backup_info.backup_path_list[0]}',
                    '--format=p',
                    f'--dbname={connection_info.details.options["dbname"]}',
                    f'--host={connection_info.details.options["host"]}',
                    f'--username={connection_info.details.options["user"]}']
    pg_dump_process = subprocess.Popen(pg_dump_args, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    # pg_dump will prompt for the password, so send it via stdin. This call will block until the process exits.
    _, stderr = pg_dump_process.communicate(str.encode(connection_info.details.options.get('password') or ''))
    if pg_dump_process.returncode != 0:
        return TaskResult(TaskStatus.FAILED, str(stderr, 'utf-8'))
    return TaskResult(TaskStatus.SUCCEEDED)


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
