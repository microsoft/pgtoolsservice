# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import logging
import os
import sys

import ptvsd

from pgsqltoolsservice.admin import AdminService
from pgsqltoolsservice.capabilities.capabilities_service import CapabilitiesService
from pgsqltoolsservice.connection import ConnectionService
from pgsqltoolsservice.disaster_recovery.disaster_recovery_service import DisasterRecoveryService
from pgsqltoolsservice.hosting import JSONRPCServer, ServiceProvider
from pgsqltoolsservice.language import LanguageService
from pgsqltoolsservice.metadata import MetadataService
from pgsqltoolsservice.object_explorer import ObjectExplorerService
from pgsqltoolsservice.query_execution import QueryExecutionService
from pgsqltoolsservice.scripting.scripting_service import ScriptingService
from pgsqltoolsservice.edit_data.edit_data_service import EditDataService
from pgsqltoolsservice.tasks import TaskService
from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.workspace import WorkspaceService

if __name__ == '__main__':
    # See if we have any arguments
    wait_for_debugger = False
    log_dir = None
    stdin = None
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
                ptvsd.enable_attach('', address=('0.0.0.0', port))
                if arg_parts[0] == '--enable-remote-debugging-wait':
                    wait_for_debugger = True
            elif arg_parts[0] == '--log-dir':
                log_dir = arg_parts[1]

    # Create the output logger
    logger = logging.getLogger('pgsqltoolsservice')
    try:
        if not log_dir:
            log_dir = os.path.dirname(sys.argv[0])
        os.makedirs(log_dir, exist_ok=True)
        handler = logging.FileHandler(os.path.join(log_dir, 'pgtoolsservice.log'))
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

    logger.info('PostgreSQL Tools Service is starting up...')

    # Create the server, but don't start it yet
    server = JSONRPCServer(stdin, std_out_wrapped, logger)

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
    service_box = ServiceProvider(server, services, logger)
    service_box.initialize()

    # Start the server
    server.start()
    server.wait_for_exit()
