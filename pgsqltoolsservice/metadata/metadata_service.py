# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.metadata.contracts import (
    MetadataListParameters, MetadataListResponse, METADATA_LIST_REQUEST)


class MetadataService(object):
    """Service for database metadata support"""

    def __init__(self):
        self._service_provider: ServiceProvider = None

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider

        # Register the request handlers with the server
        self._service_provider.server.set_request_handler(
            METADATA_LIST_REQUEST, self._handle_metadata_list_request
        )

        if self._service_provider.logger is not None:
            self._service_provider.logger.info('Metadata service successfully initialized')

    # REQUEST HANDLERS #####################################################

    def _handle_metadata_list_request(self, request_context: RequestContext, params: MetadataListParameters) -> None:
        request_context.send_response(MetadataListResponse())
