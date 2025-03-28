# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

from ossdbtoolsservice.capabilities.connection_options.pg_connection_options import (
    capabilities as PGServerCapabilities,
)
from ossdbtoolsservice.capabilities.contracts import (
    CAPABILITIES_REQUEST,
    INITIALIZE_REQUEST,
    CapabilitiesRequestParams,
    CapabilitiesResult,
    CompletionOptions,
    InitializeRequestParams,
    InitializeResult,
    ServerCapabilities,
    TextDocumentSyncKind,
)
from ossdbtoolsservice.hosting import RequestContext, Service, ServiceProvider
from ossdbtoolsservice.utils import constants

SERVER_CAPABILITIES_MAP = {constants.PG_PROVIDER_NAME: PGServerCapabilities}


class CapabilitiesService(Service):
    """Defines the capabilities supported by PG Tools
    including language service and DMP support"""

    def __init__(self) -> None:
        super().__init__()

    def register(self, service_provider: ServiceProvider) -> None:
        self._service_provider = service_provider

        self._service_provider.server.set_request_handler(
            CAPABILITIES_REQUEST, self._handle_dmp_capabilities_request
        )
        self._service_provider.server.set_request_handler(
            INITIALIZE_REQUEST, self._handle_initialize_request
        )

    def _handle_dmp_capabilities_request(
        self,
        request_context: RequestContext,
        params: Optional[CapabilitiesRequestParams],
    ) -> None:
        """
        Sends the capabilities of the tools service data protocol features
        :param request_context: Context of the request
        :param params: Parameters for the capabilities request
        """
        provider: str = self.service_provider.provider
        capabilities = SERVER_CAPABILITIES_MAP[provider]

        result = CapabilitiesResult(capabilities)

        # Send the response
        request_context.send_response(result)

    @staticmethod
    def _handle_initialize_request(
        request_context: RequestContext, params: Optional[InitializeRequestParams]
    ) -> None:
        """
        Sends the capabilities of the tools service language features
        :param request_context: Context for the request
        :param params: Initialization request parameters
        """
        capabilities = ServerCapabilities(
            text_document_sync=TextDocumentSyncKind.INCREMENTAL,
            definition_provider=True,
            references_provider=False,
            document_formatting_provider=True,
            document_range_formatting_provider=True,
            document_highlight_provider=False,
            hover_provider=False,
            completion_provider=CompletionOptions(True, [".", "-", ":", "\\", "[", '"']),
            signature_help_provider=None,
            document_symbol_provider=False,
            workspace_symbol_provider=False,
        )
        result = InitializeResult(capabilities)

        # Send the request
        request_context.send_response(result)
