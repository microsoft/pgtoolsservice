# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing the disaster recovery service,
including backup and restore functionality"""

import functools
import os
import subprocess
import sys
from typing import Any

import inflection

from ossdbtoolsservice.connection import OwnerConnectionInfo
from ossdbtoolsservice.connection.connection_service import ConnectionService
from ossdbtoolsservice.disaster_recovery.contracts import (
    BACKUP_REQUEST,
    RESTORE_REQUEST,
    BackupParams,
    BackupType,
    RestoreParams,
)
from ossdbtoolsservice.hosting import RequestContext, Service, ServiceProvider
from ossdbtoolsservice.tasks import Task, TaskResult, TaskStatus
from ossdbtoolsservice.tasks.task_service import TaskService
from ossdbtoolsservice.utils import constants


class DisasterRecoveryService(Service):
    """Manage backup and restore"""

    def __init__(self) -> None:
        super().__init__()

    def register(self, service_provider: ServiceProvider) -> None:
        """Register handlers with the service provider"""
        self._service_provider = service_provider

        # Register the handlers for the service
        self._service_provider.server.set_request_handler(
            BACKUP_REQUEST, self.handle_backup_request
        )
        self._service_provider.server.set_request_handler(
            RESTORE_REQUEST, self.handle_restore_request
        )

    def handle_backup_request(
        self, request_context: RequestContext, params: BackupParams
    ) -> None:
        """
        Respond to backup/backup requests by performing a backup

        :param request_context: The request context
        :param params: The BackupParams object for this request
        """
        owner_uri = params.owner_uri
        if owner_uri is None:
            request_context.send_error("Owner URI is required")
            return
        connection_info: OwnerConnectionInfo | None = self.service_provider.get(
            constants.CONNECTION_SERVICE_NAME, ConnectionService
        ).get_connection_info(owner_uri)
        if connection_info is None:
            request_context.send_error(
                "No connection corresponding to the given owner URI"
            )  # TODO: Localize
            return
        provider: str = self.service_provider.provider
        host = connection_info.connection_details.server_name
        database = connection_info.connection_details.database_name

        task = Task(
            "Backup",
            f"Host: {host}, Database: {database}",
            provider,
            host,
            database,
            request_context,  # TODO: Localize
            functools.partial(_perform_backup, connection_info, params),
        )
        self.service_provider.get(constants.TASK_SERVICE_NAME, TaskService).start_task(task)
        request_context.send_response({})

    def handle_restore_request(
        self, request_context: RequestContext, params: RestoreParams
    ) -> None:
        """
        Respond to restore/restore requests by performing a restore
        """
        owner_uri = params.owner_uri
        if owner_uri is None:
            request_context.send_error("Owner URI is required")
            return
        connection_info: OwnerConnectionInfo | None = self.service_provider.get(
            constants.CONNECTION_SERVICE_NAME, ConnectionService
        ).get_connection_info(owner_uri)
        if connection_info is None:
            request_context.send_error(
                "No connection corresponding to the given owner URI"
            )  # TODO: Localize
            return
        provider: str = self.service_provider.provider
        host = connection_info.connection_details.server_name
        database = connection_info.connection_details.database_name
        task = Task(
            "Restore",
            f"Host: {host}, Database: {database}",
            provider,
            host,
            database,
            request_context,  # TODO: Localize
            functools.partial(_perform_restore, connection_info, params),
        )
        self.service_provider.get(constants.TASK_SERVICE_NAME, TaskService).start_task(task)
        request_context.send_response({})


def _perform_backup_restore(
    connection_info: OwnerConnectionInfo,
    process_args: list[str],
    options: dict[str, Any],
    task: Task,
) -> TaskResult:
    """Call out to pg_dump or pg_restore using the arguments given and
    additional arguments built from the given options dict"""
    for option, value in options.items():
        # Don't add the option to the arguments if it is not set
        if value is None or value is False:
            continue
        # Replace underscores with dashes in the option name
        key_name = inflection.dasherize(option)
        if value is True:
            # The option is a boolean flag, so just add the option
            process_args.insert(-1, f"--{key_name}")
        else:
            # The option has a value, so add the flag with its value
            process_args.insert(-1, f"--{key_name}={value}")
    with task.cancellation_lock:
        if task.canceled:
            return TaskResult(TaskStatus.CANCELED)
        dump_restore_process: subprocess.Popen | None = None
        try:
            password = connection_info.connection_details.options.get("password") or ""
            os.putenv("PGPASSWORD", str(password))

            # Set the executable bit on the file
            # Check if process_args[0] file exists
            if len(process_args) > 0 and os.path.isfile(process_args[0]):
                os.chmod(process_args[0], 0o755)

            dump_restore_process = subprocess.Popen(process_args, stderr=subprocess.PIPE)
            task.on_cancel = dump_restore_process.terminate
            _, stderr = dump_restore_process.communicate()
        except subprocess.SubprocessError as err:
            if dump_restore_process:
                dump_restore_process.kill()
            return TaskResult(TaskStatus.FAILED, str(err))
    if dump_restore_process.returncode != 0:
        return TaskResult(TaskStatus.FAILED, str(stderr, "utf-8"))
    return TaskResult(TaskStatus.SUCCEEDED)


def _perform_backup(
    connection_info: OwnerConnectionInfo, params: BackupParams, task: Task
) -> TaskResult:
    """Call out to pg_dump to do a backup"""
    backup_info = params.backup_info
    if backup_info is None:
        return TaskResult(TaskStatus.FAILED, "Backup info is required")

    backup_type = backup_info.type
    if backup_type is None:
        return TaskResult(TaskStatus.FAILED, "Backup type is required")
    try:
        pg_dump_location = _get_pg_exe_path("pg_dump", connection_info.server_version)
    except ValueError as e:
        return TaskResult(TaskStatus.FAILED, str(e))
    pg_dump_args = [
        pg_dump_location,
        f"--file={backup_info.path}",
        f"--format={_BACKUP_FORMAT_MAP[backup_type]}",
    ]

    pg_dump_args += _get_backup_restore_connection_params(
        connection_info.connection_details.options
    )
    # Remove the options that were already used,
    # and pass the rest so that they can be automatically serialized
    options = params.backup_info.__dict__.copy()
    del options["path"]
    del options["type"]
    return _perform_backup_restore(connection_info, pg_dump_args, options, task)


def _perform_restore(
    connection_info: OwnerConnectionInfo, params: RestoreParams, task: Task
) -> TaskResult:
    """Call out to pg_restore to restore from a backup"""
    options = params.options
    if options is None:
        return TaskResult(TaskStatus.FAILED, "Options are required")

    path = options.path
    if path is None:
        return TaskResult(TaskStatus.FAILED, "Path is required")

    try:
        pg_restore_location = _get_pg_exe_path("pg_restore", connection_info.server_version)
    except ValueError as e:
        return TaskResult(TaskStatus.FAILED, str(e))
    pg_restore_args = [pg_restore_location]
    pg_restore_args += _get_backup_restore_connection_params(
        connection_info.connection_details.options
    )
    pg_restore_args.append(path)
    # Remove the options that were already used,
    # and pass the rest so that they can be automatically serialized
    options_dict = options.__dict__.copy()
    del options_dict["path"]
    return _perform_backup_restore(connection_info, pg_restore_args, options_dict, task)


def _get_backup_restore_connection_params(connection_options: dict) -> list[str]:
    params = [
        f"--dbname={connection_options['dbname']}",
        f"--host={connection_options['host']}",
        f"--username={connection_options['user']}",
    ]
    port = connection_options.get("port")
    if port is not None:
        params.append(f"--port={port}")
    return params


def _get_pg_exe_path(exe_name: str, server_version: tuple[int, int, int]) -> str:
    """
    Find the path to the given PostgreSQL utility executable
    for the current operating system in a server specific version folder

    :param exe_name: The name of the program to find (without .exe). e.g. 'pg_dump'
    :param server_version: Tuple of the connected server version components
        (major, minor, ignored)
    :returns: The path to the requested executable
    :raises ValueError: if there is no file corresponding to the given exe_name
    """

    base_location = os.path.join(os.path.dirname(sys.argv[0]), "pg_exes")
    platform = sys.platform
    if platform == "win32":
        os_root = os.path.join(base_location, "win")
        path_suffix = exe_name + ".exe"
    elif platform == "darwin":
        os_root = os.path.join(base_location, "mac")
        path_suffix = os.path.join("bin", exe_name)
    else:
        os_root = os.path.join(base_location, "linux")
        path_suffix = os.path.join("bin", exe_name)

    # Get the list of folders in the os specific root folder
    all_folders: list[str] = [os.path.normpath(x[0]) for x in os.walk(os_root)]
    for folder in all_folders:
        folderName = os.path.basename(folder)
        version = folderName.split(".")
        # Get the major version value
        try:
            major = int(version[0])
        except ValueError:
            major = 0
        minor = 0
        # Set minor version if version length is more than 1 (ex 9.5, 9.6)
        if len(version) > 1:
            try:
                minor = int(version[1])
            except ValueError:
                minor = 0

        if major == int(server_version[0]) and minor == server_version[1]:
            exe_path = os.path.join(folder, path_suffix)
            if not os.path.exists(exe_path):
                raise ValueError(f"Could not find executable file {exe_path}")
            return exe_path

    version_string = ".".join(str(ver) for ver in server_version)
    raise ValueError(
        f"Exe folder {os_root} does not contain {exe_name} for version {version_string}"
    )


# Map from backup types to the corresponding pg_dump format option value
_BACKUP_FORMAT_MAP = {
    BackupType.DIRECTORY: "d",
    BackupType.PG_DUMP: "c",
    BackupType.PLAIN_TEXT: "p",
    BackupType.TAR: "t",
}
