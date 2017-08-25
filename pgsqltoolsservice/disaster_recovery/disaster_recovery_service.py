# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing the disaster recovery service, including backup and restore functionality"""

import functools
import os
import subprocess
import sys
from typing import Any, List, Dict

import inflection

from pgsqltoolsservice.connection import ConnectionInfo
from pgsqltoolsservice.disaster_recovery.contracts import BACKUP_REQUEST, BackupParams, BackupType, RESTORE_REQUEST, RestoreParams
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
        self._service_provider.server.set_request_handler(RESTORE_REQUEST, self.handle_restore_request)

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
        self._service_provider[constants.TASK_SERVICE_NAME].start_task(task)
        request_context.send_response({})

    def handle_restore_request(self, request_context: RequestContext, params: RestoreParams) -> None:
        """
        Respond to disasterrecovery/restore requests by performing a restore
        """
        connection_info: ConnectionInfo = self._service_provider[constants.CONNECTION_SERVICE_NAME].get_connection_info(params.owner_uri)
        if connection_info is None:
            request_context.send_error('No connection corresponding to the given owner URI')  # TODO: Localize
            return
        host = connection_info.details.options['host']
        database = connection_info.details.options['dbname']
        task = Task('Restore', f'Host: {host}, Database: {database}', constants.PROVIDER_NAME, host, database, request_context,  # TODO: Localize
                    functools.partial(_perform_restore, connection_info, params))
        self._service_provider[constants.TASK_SERVICE_NAME].start_task(task)
        request_context.send_response({})


def _perform_backup_restore(connection_info: ConnectionInfo, process_args: List[str], options: Dict[str, Any], task: Task):
    """Call out to pg_dump or pg_restore using the arguments given and additional arguments built from the given options dict"""
    for option, value in options.items():
        # Don't add the option to the arguments if it is not set
        if value is None or value is False:
            continue
        # Replace underscores with dashes in the option name
        key_name = inflection.dasherize(option)
        if value is True:
            # The option is a boolean flag, so just add the option
            process_args.append(f'--{key_name}')
        else:
            # The option has a value, so add the flag with its value
            process_args.append(f'--{key_name}={value}')
    with task.cancellation_lock:
        if task.canceled:
            return TaskResult(TaskStatus.CANCELED)
        dump_restore_process = subprocess.Popen(process_args, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        task.on_cancel = dump_restore_process.terminate
    # pg_dump and pg_restore will prompt for the password, so send it via stdin. This call will block until the process exits.
    _, stderr = dump_restore_process.communicate(str.encode(connection_info.details.options.get('password') or ''))
    if dump_restore_process.returncode != 0:
        return TaskResult(TaskStatus.FAILED, str(stderr, 'utf-8'))
    return TaskResult(TaskStatus.SUCCEEDED)


def _perform_backup(connection_info: ConnectionInfo, params: BackupParams, task: Task) -> TaskResult:
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
    # Remove the options that were already used, and pass the rest so that they can be automatically serialized
    options = params.backup_info.__dict__.copy()
    del options['path']
    del options['type']
    return _perform_backup_restore(connection_info, pg_dump_args, options, task)


def _perform_restore(connection_info: ConnectionInfo, params: RestoreParams, task: Task) -> TaskResult:
    """Call out to pg_restore to restore from a backup"""
    try:
        pg_dump_location = _get_pg_exe_path('pg_restore')
    except ValueError as e:
        return TaskResult(TaskStatus.FAILED, str(e))
    pg_restore_args = [pg_dump_location,
                       f'--dbname={connection_info.details.options["dbname"]}',
                       f'--host={connection_info.details.options["host"]}',
                       f'--username={connection_info.details.options["user"]}',
                       f'{params.options.path}']
    # Remove the options that were already used, and pass the rest so that they can be automatically serialized
    options = params.options.__dict__.copy()
    del options['path']
    return _perform_backup_restore(connection_info, pg_restore_args, options, task)


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


# Map from backup types to the corresponding pg_dump format option value
_BACKUP_FORMAT_MAP = {
    BackupType.DIRECTORY: 'd',
    BackupType.PG_DUMP: 'c',
    BackupType.PLAIN_TEXT: 'p',
    BackupType.TAR: 't'
}
