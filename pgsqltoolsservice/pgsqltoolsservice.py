# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import sys

from pgsqltoolsservice.connection import ConnectionService
from pgsqltoolsservice.hosting import JSONRPCServer, ServiceProvider

if __name__ == '__main__':
    # Create the output logger
    logger = logging.getLogger('pgsqltoolsservice')
    handler = logging.Handler('pgsqltoolsservice.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.info('PostgreSQL Tools Service is starting up...')

    # Create the server, but don't start it yet
    server = JSONRPCServer(sys.stdin, sys.stdout)

    # Create the service provider and add the providers to it
    service_box = ServiceProvider(server, logger)
    service_box.set_service('connection', ConnectionService)

