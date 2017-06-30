# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from typing import List
from urllib.parse import quote 

import psycopg2
import psycopg2.errorcodes

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.metadata.contracts import ObjectMetadata
from pgsqltoolsservice.scripting.contracts import (
    ScriptAsParameters, ScriptAsResponse, SCRIPTAS_REQUEST)
import pgsqltoolsservice.utils as utils

class ScriptingService(object):
    """Service for scripting database objects"""

    def __init__(self):
        self._service_provider: ServiceProvider = None


    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider

        # Register the request handlers with the server
        self._service_provider.server.set_request_handler(
            SCRIPTAS_REQUEST, self._handle_scriptas_request
        )

        if self._service_provider.logger is not None:
            self._service_provider.logger.info('Scripting service successfully initialized')

    # REQUEST HANDLERS #####################################################

    def _handle_scriptas_request(self, request_context: RequestContext, params: ScriptAsParameters) -> None:
        if params.operation == 0:
            script = 'SELECT *\nFROM ' + params.metadata['schema'] + '."' + params.metadata['name'] + '"\nLIMIT 1000\n'
        else:
             script = 'Coming soon.  Check back in an upcoming release'
        request_context.send_response(ScriptAsResponse(params.owner_uri, script))
 