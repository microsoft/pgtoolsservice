# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import logging
import sys

import ptvsd

from pgsqltoolsservice.admin import AdminService
from pgsqltoolsservice.capabilities import CapabilitiesService
from pgsqltoolsservice.connection import ConnectionService
from pgsqltoolsservice.hosting import JSONRPCServer, ServiceProvider
from pgsqltoolsservice.language import LanguageService
from pgsqltoolsservice.metadata import MetadataService
from pgsqltoolsservice.object_explorer import ObjectExplorerService
from pgsqltoolsservice.query_execution import QueryExecutionService
from pgsqltoolsservice.scripting import ScriptingService
from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.workspace import WorkspaceService

if __name__ == '__main__':
    # Create the output logger
    logger = logging.getLogger('pgsqltoolsservice')
    # TODO: Fix logging to work with release builds on mac
    # handler = logging.FileHandler('pgsqltoolsservice.log')
    # formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    # handler.setFormatter(formatter)
    # logger.addHandler(handler)
    logger.addHandler(logging.NullHandler())
    logger.setLevel(logging.DEBUG)

    # See if we have any arguments
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
        constants.LANGUAGE_SERVICE_NAME: LanguageService,
        constants.METADATA_SERVICE_NAME: MetadataService,
        constants.OBJECT_EXPLORER_NAME: ObjectExplorerService,
        constants.QUERY_EXECUTION_SERVICE_NAME: QueryExecutionService,
        constants.SCRIPTING_SERVICE_NAME: ScriptingService,
        constants.WORKSPACE_SERVICE_NAME: WorkspaceService,
    }
    service_box = ServiceProvider(server, services, logger)
    service_box.initialize()

    # Start the server
    server.start()
    server.wait_for_exit()
