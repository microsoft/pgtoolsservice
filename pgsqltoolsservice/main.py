# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import logging
import sys

from pgsqltoolsservice.capabilities import CapabilitiesService
from pgsqltoolsservice.connection import ConnectionService
from pgsqltoolsservice.hosting import JSONRPCServer, ServiceProvider

if __name__ == '__main__':
    # See if we have any arguments
    stdin = None
    if len(sys.argv) > 1:
        for arg in sys.argv:
            arg_parts = arg.split('=')
            if arg_parts[0] == 'input':
                stdin = io.open(arg_parts[1], 'rb', buffering=0)

    # Wrap standard in and out in io streams to add readinto support
    if stdin is None:
        stdin = io.open(sys.stdin.fileno(), 'rb', buffering=0, closefd=False)

    std_out_wrapped = io.open(sys.stdout.fileno(), 'wb', buffering=0, closefd=False)

    # Create the output logger
    logger = logging.getLogger('pgsqltoolsservice')
    handler = logging.FileHandler('pgsqltoolsservice.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.info('PostgreSQL Tools Service is starting up...')

    # Create the server, but don't start it yet
    server = JSONRPCServer(stdin, std_out_wrapped, logger)

    # Create the service provider and add the providers to it
    service_box = ServiceProvider(server, logger)
    service_box.set_service('capabilities', CapabilitiesService)
    service_box.set_service('connection', ConnectionService)

    # Start the server
    server.start()
    server.wait_for_exit()



