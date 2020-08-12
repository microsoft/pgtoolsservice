# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import logging
import os
import sys

import ptvsd

from ossdbtoolsservice.admin import AdminService
from ossdbtoolsservice.capabilities.capabilities_service import CapabilitiesService
from ossdbtoolsservice.connection import ConnectionService
from ossdbtoolsservice.disaster_recovery.disaster_recovery_service import DisasterRecoveryService
from ossdbtoolsservice.hosting import JSONRPCServer, ServiceProvider
from ossdbtoolsservice.language import LanguageService
from ossdbtoolsservice.metadata import MetadataService
from ossdbtoolsservice.object_explorer import ObjectExplorerService
from ossdbtoolsservice.query_execution import QueryExecutionService
from ossdbtoolsservice.scripting.scripting_service import ScriptingService
from ossdbtoolsservice.edit_data.edit_data_service import EditDataService
from ossdbtoolsservice.tasks import TaskService
from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.workspace import WorkspaceService


def _create_server(input_stream, output_stream, server_logger, provider):
    # Create the server, but don't start it yet
    rpc_server = JSONRPCServer(input_stream, output_stream, server_logger)

    # Create the service provider and add the providers to it
    services = {
        constants.ADMIN_SERVICE_NAME: AdminService,
        constants.CAPABILITIES_SERVICE_NAME: CapabilitiesService,
        constants.CONNECTION_SERVICE_NAME: ConnectionService,
        constants.DISASTER_RECOVERY_SERVICE_NAME: DisasterRecoveryService,
        constants.LANGUAGE_SERVICE_NAME: LanguageService,
        constants.METADATA_SERVICE_NAME: MetadataService,
        constants.OBJECT_EXPLORER_NAME: ObjectExplorerService,
        constants.QUERY_EXECUTION_SERVICE_NAME: QueryExecutionService,
        constants.SCRIPTING_SERVICE_NAME: ScriptingService,
        constants.WORKSPACE_SERVICE_NAME: WorkspaceService,
        constants.EDIT_DATA_SERVICE_NAME: EditDataService,
        constants.TASK_SERVICE_NAME: TaskService
    }
    service_box = ServiceProvider(rpc_server, services, provider, server_logger)
    service_box.initialize()
    return rpc_server


if __name__ == '__main__':
    # See if we have any arguments
    wait_for_debugger = False
    log_dir = None
    stdin = None
    # Setting a default provider name to test PG extension
    provider_name = constants.PG_PROVIDER_NAME
    if len(sys.argv) > 1:
        for arg in sys.argv:
            arg_parts = arg.split('=')
            if arg_parts[0] == 'input':
                stdin = io.open(arg_parts[1], 'rb', buffering=0)
            elif arg_parts[0] == '--enable-remote-debugging' or arg_parts[0] == '--enable-remote-debugging-wait':
                port = 3000
                try:
                    port = int(arg_parts[1])
                except IndexError:
                    pass
                try:
                    ptvsd.enable_attach(address=('0.0.0.0', port))
                except BaseException:
                    # If port 3000 is used, try another debug port
                    port += 1
                    ptvsd.enable_attach(address=('0.0.0.0', port))
                if arg_parts[0] == '--enable-remote-debugging-wait':
                    wait_for_debugger = True
            elif arg_parts[0] == '--log-dir':
                log_dir = arg_parts[1]
            elif arg_parts[0] == 'provider':
                provider_name = arg_parts[1]
                # Check if we support the given provider
                supported = provider_name in constants.SUPPORTED_PROVIDERS
                if not supported:
                    raise AssertionError("{} is not a supported provider".format(str(provider_name)))

    # Create the output logger
    logger = logging.getLogger('ossdbtoolsservice')
    try:
        if not log_dir:
            log_dir = os.path.dirname(sys.argv[0])
        os.makedirs(log_dir, exist_ok=True)
        handler = logging.FileHandler(os.path.join(log_dir, 'ossdbtoolsservice.log'))
    except Exception:
        handler = logging.NullHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # Wait for the debugger to attach if needed
    if wait_for_debugger:
        logger.debug('Waiting for a debugger to attach...')
        ptvsd.wait_for_attach()

    # Wrap standard in and out in io streams to add readinto support
    if stdin is None:
        stdin = io.open(sys.stdin.fileno(), 'rb', buffering=0, closefd=False)

    std_out_wrapped = io.open(sys.stdout.fileno(), 'wb', buffering=0, closefd=False)

    logger.info('{0} Tools Service is starting up...'.format(provider_name))

    # Create the server, but don't start it yet
    server = _create_server(stdin, std_out_wrapped, logger, provider_name)

    # Start the server
    server.start()
    server.wait_for_exit()
