# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Callable, List   # noqa

from pgsqltoolsservice.hosting import NotificationContext, ServiceProvider
from pgsqltoolsservice.workspace.contracts import (
    DID_CHANGE_CONFIG_NOTIFICATION, DidChangeConfigurationParams,
    DID_CHANGE_TEXT_DOCUMENT_NOTIFICATION, DidChangeTextDocumentParams,
    DID_OPEN_TEXT_DOCUMENT_NOTIFICATION, DidOpenTextDocumentParams,
    DID_CLOSE_TEXT_DOCUMENT_NOTIFICATION, DidCloseTextDocumentParams,
    PGSQLConfiguration
)
from pgsqltoolsservice.workspace.script_file import ScriptFile
from pgsqltoolsservice.workspace.workspace import Workspace


class WorkspaceService:
    """
    Class for handling requests/events that deal with the sate of the workspace including opening
    and closing of files, the changing of configuration, etc.
    """

    def __init__(self):
        self._service_provider: ServiceProvider = None
        self._workspace: Workspace = None

        # Create a workspace that will handle state for the session
        self._workspace = Workspace()
        self._configuration: PGSQLConfiguration = PGSQLConfiguration()

        # Setup callbacks for the various events we can receive
        self._config_change_callbacks: List[Callable[PGSQLConfiguration]] = []
        self._text_change_callbacks: List[Callable[ScriptFile]] = []
        self._text_open_callbacks: List[Callable[ScriptFile]] = []
        self._text_close_callbacks: List[Callable[ScriptFile]] = []

    def register(self, service_provider: ServiceProvider) -> None:
        self._service_provider = service_provider

        # Register the handlers for when changes to the workspace occur
        self._service_provider.server.set_notification_handler(DID_CHANGE_TEXT_DOCUMENT_NOTIFICATION,
                                                               self._handle_did_change_text_doc)
        self._service_provider.server.set_notification_handler(DID_OPEN_TEXT_DOCUMENT_NOTIFICATION,
                                                               self._handle_did_open_text_doc)
        self._service_provider.server.set_notification_handler(DID_CLOSE_TEXT_DOCUMENT_NOTIFICATION,
                                                               self._handle_did_close_text_doc)

        # Register handler for when the configuration changes
        self._service_provider.server.set_notification_handler(DID_CHANGE_CONFIG_NOTIFICATION,
                                                               self._handle_did_change_config)

    # PROPERTIES ###########################################################
    @property
    def configuration(self) -> PGSQLConfiguration:
        return self._configuration

    # METHODS ##############################################################
    def register_config_change_callback(self, task: Callable[PGSQLConfiguration]) -> None:
        self._config_change_callbacks.append(task)

    def register_text_change_callback(self, task: Callable[ScriptFile]) -> None:
        self._text_change_callbacks.append(task)

    def register_text_close_callback(self, task: Callable[ScriptFile]) -> None:
        self._text_close_callbacks.append(task)

    def register_text_open_callback(self, task: Callable[ScriptFile]) -> None:
        self._text_open_callbacks.append(task)

    # REQUEST HANDLERS #####################################################
    def _handle_did_change_config(
            self,
            notification_context: NotificationContext,
            params: DidChangeConfigurationParams
    ) -> None:
        """
        Handles the configuration change event by storing the new configuration and calling all
        registered config change callbacks
        :param notification_context: Context of the notification
        :param params: Parameters from the notification
        """
        self._configuration = params.settings
        for callback in self._config_change_callbacks:
            callback(self._configuration)

    def _handle_did_change_text_doc(
            self,
            notification_context: NotificationContext,
            params: DidChangeTextDocumentParams
    ) -> None:
        """
        Handles text document change notifications
        :param notification_context: Context of the notification
        :param params: Parameters of the notification
        """
        # Skip processing if the file is an SCM file or the file isn't opened
        if self._is_scm_path(params.text_document.uri) or not self._workspace.contains_file(params.text_document.uri):
            return

        script_file: ScriptFile = self._workspace.get_file(params.text_document.uri)

        # Apply the changes to the document
        for text_change in params.content_changes:
            script_file.apply_change(text_change)

        # Propagate the changes to the registered callbacks
        for callback in self._text_change_callbacks:
            callback(script_file)

    def _handle_did_open_text_doc(
            self,
            notification_context: NotificationContext,
            params: DidOpenTextDocumentParams
    ) -> None:
        """
        Handles when a file is opened in the workspace. The event is propagated to the registered
        file open callbacks
        :param notification_context: Context of the notification
        :param params: Parameters from the notification
        """
        # Skip processing if the file is an SCM file
        if self._is_scm_path(params.text_document.uri):
            return

        # Open a new ScriptFile with the initial buffer provided
        opened_file: ScriptFile = self._workspace.open_file(params.text_document.uri, params.text_document.text)

        # Propagate the notification to the registered callbacks
        for callback in self._text_open_callbacks:
            callback(opened_file)

    def _handle_did_close_text_doc(
            self,
            notification_context: NotificationContext,
            params: DidCloseTextDocumentParams
    ) -> None:
        """
        Handles when a file is closed in the workspace. The event is propagated to the registered
        file close callbacks
        :param notification_context: Context of the notification
        :param params: Parameters from the notification
        """
        # Skip processing if this file is an SCM file or not open
        if self._is_scm_path(params.text_document.uri) or not self._workspace.contains_file(params.text_document.uri):
            return

        # File is open. Trash the existing document from out mapping
        closed_file: ScriptFile = self._workspace.close_file(params.text_document.uri)

        # Propagate the notification to the registered callbacks
        for callback in self._text_close_callbacks:
            callback(closed_file)

    # IMPLEMENTATION DETAILS ###############################################

    @staticmethod
    def _is_scm_path(file_uri: str):
        """
        If the URI is prefixed with git: then we want to skip processing the file
        :param file_uri: URI for the file to check
        """
        return file_uri.startswith('git:')
