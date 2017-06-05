# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.workspace.contracts import (
    did_change_text_document_notification, DidChangeTextDocumentParams,
    did_open_text_document_notification, DidOpenTextDocumentParams,
    did_close_text_document_notification, DidCloseTextDocumentParams
)
from pgsqltoolsservice.workspace.workspace import Workspace

class WorkspaceService:
    """
    Class for handling requests/events that deal with the sate of the workspace including opening
    and closing of files, the changing of configuration, etc.
    """

    def __init__(self, service_provider: ServiceProvider):
        self._service_provider: ServiceProvider = service_provider
        self._workspace: Workspace = None

        # Setup callbacks for the various events we can receive
        self._config_change_callbacks = []
        self._text_change_callback = []
        self._text_open_callback = []
        self._text_close_callback = []

    def initialize(self) -> None:
        # Create a workspace that will handle state for the session
        self._workspace = Workspace()

        # Register the handlers for when changes to the workspace occur
        self._service_provider.server.set_notification_handler(did_change_text_document_notification,
                                                               self._handle_did_change_text_doc)
        self._service_provider.server.set_notification_handler(did_open_text_document_notification,
                                                               self._handle_did_open_text_doc)
        self._service_provider.server.set_notification_handler(did_close_text_document_notification,
                                                               self._handle_did_close_text_doc)

    # REQUEST HANDLERS #####################################################
    def _handle_did_change_text_doc(self, request_context: RequestContext, params: DidChangeTextDocumentParams):
        pass

    def _handle_did_open_text_doc(self, request_context: RequestContext, params: DidOpenTextDocumentParams):
        pass

    def _handle_did_close_text_doc(self, request_context: RequestContext, params: DidCloseTextDocumentParams):
        pass
