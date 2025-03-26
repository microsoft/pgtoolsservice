# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from logging import Logger  # noqa
from typing import Callable, List, Optional  # noqa

from ossdbtoolsservice.hosting import (
    NotificationContext,
    ServiceProvider,
    Service,
)
from ossdbtoolsservice.workspace.contracts import (
    DID_CHANGE_CONFIG_NOTIFICATION,
    DidChangeConfigurationParams,
    DID_CHANGE_TEXT_DOCUMENT_NOTIFICATION,
    DidChangeTextDocumentParams,
    DID_OPEN_TEXT_DOCUMENT_NOTIFICATION,
    DidOpenTextDocumentParams,
    DID_CLOSE_TEXT_DOCUMENT_NOTIFICATION,
    DidCloseTextDocumentParams,
    Configuration,
    Range,
)
from ossdbtoolsservice.workspace.script_file import ScriptFile
from ossdbtoolsservice.workspace.workspace import Workspace


class WorkspaceService(Service):
    """
    Class for handling requests/events that deal with the
    sate of the workspace including opening
    and closing of files, the changing of configuration, etc.
    """

    def __init__(self) -> None:
        super().__init__()

        # Create a workspace that will handle state for the session
        self._workspace = Workspace()
        self._configuration: Configuration = Configuration()

        # Setup callbacks for the various events we can receive
        self._config_change_callbacks: list[Callable[[Configuration], None]] = []
        self._text_change_callbacks: list[Callable[[ScriptFile], None]] = []
        self._text_open_callbacks: list[Callable[[ScriptFile], None]] = []
        self._text_close_callbacks: list[Callable[[ScriptFile], None]] = []

    def register(self, service_provider: ServiceProvider) -> None:
        self._service_provider = service_provider
        self._logger = service_provider.logger
        self._server = service_provider.server

        # Register the handlers for when changes to the workspace occur
        self._server.set_notification_handler(
            DID_CHANGE_TEXT_DOCUMENT_NOTIFICATION, self._handle_did_change_text_doc
        )
        self._server.set_notification_handler(
            DID_OPEN_TEXT_DOCUMENT_NOTIFICATION, self._handle_did_open_text_doc
        )
        self._server.set_notification_handler(
            DID_CLOSE_TEXT_DOCUMENT_NOTIFICATION, self._handle_did_close_text_doc
        )

        # Register handler for when the configuration changes
        self._service_provider.server.set_notification_handler(
            DID_CHANGE_CONFIG_NOTIFICATION, self._handle_did_change_config
        )

    # PROPERTIES ###########################################################
    @property
    def configuration(self) -> Configuration:
        return self._configuration

    @property
    def workspace(self) -> Workspace:
        """Gets the current workspace"""
        return self._workspace

    # METHODS ##############################################################
    def register_config_change_callback(self, task: Callable[[Configuration], None]) -> None:
        self._config_change_callbacks.append(task)

    def register_text_change_callback(self, task: Callable[[ScriptFile], None]) -> None:
        self._text_change_callbacks.append(task)

    def register_text_close_callback(self, task: Callable[[ScriptFile], None]) -> None:
        self._text_close_callbacks.append(task)

    def register_text_open_callback(self, task: Callable[[ScriptFile], None]) -> None:
        self._text_open_callbacks.append(task)

    def get_text(self, file_uri: str, selection_range: Optional[Range]) -> str:
        """
        Get the requested text selection, as a string, for a document

        :param file_uri: The URI of the requested file
        :param selection_data: An object containing information about
            which part of the file to return,
            or None for the whole file
        :raises ValueError: If there is no file matching the given URI
        """
        open_file = self._workspace.get_file(file_uri)
        if open_file is None:
            raise ValueError("No file corresponding to the given URI")
        if selection_range is None:
            return open_file.get_all_text()
        else:
            return open_file.get_text_in_range(selection_range)

    # REQUEST HANDLERS #####################################################
    def _handle_did_change_config(
        self, notification_context: NotificationContext, params: DidChangeConfigurationParams
    ) -> None:
        """
        Handles the configuration change event by storing the
        new configuration and calling all
        registered config change callbacks
        :param notification_context: Context of the notification
        :param params: Parameters from the notification
        """
        if params.settings is None:
            self._log_warning(f"No settings provided in configuration change: {params}")
            return
        self._configuration = params.settings
        for callback in self._config_change_callbacks:
            callback(self._configuration)

    def _handle_did_change_text_doc(
        self, notification_context: NotificationContext, params: DidChangeTextDocumentParams
    ) -> None:
        """
        Handles text document change notifications
        :param notification_context: Context of the notification
        :param params: Parameters of the notification
        """
        try:
            # Skip processing if the file isn't opened
            if params.text_document is None:
                self._log_warning(f"No text document provided in change: {params}")
                return
            uri = params.text_document.uri
            if uri is None:
                self._log_warning(f"No URI provided in text document change: {params}")
                return
            script_file: ScriptFile | None = self._workspace.get_file(uri)
            if script_file is None:
                return

            # Apply the changes to the document
            for text_change in params.content_changes:
                script_file.apply_change(text_change)

            # Propagate the changes to the registered callbacks
            for callback in self._text_change_callbacks:
                callback(script_file)
        except Exception as e:
            if self._logger is not None:
                self._logger.exception(f"Exception caught during text doc change: {e}")

    def _handle_did_open_text_doc(
        self, notification_context: NotificationContext, params: DidOpenTextDocumentParams
    ) -> None:
        """
        Handles when a file is opened in the workspace.
        The event is propagated to the registered
        file open callbacks
        :param notification_context: Context of the notification
        :param params: Parameters from the notification
        """
        try:
            if params.text_document is None:
                self._log_warning(f"No text document provided in change: {params}")
                return
            uri = params.text_document.uri
            if uri is None:
                self._log_warning(f"No URI provided in text document change: {params}")
                return
            # Open a new ScriptFile with the initial buffer provided
            opened_file: ScriptFile | None = self._workspace.open_file(
                uri, params.text_document.text
            )
            if opened_file is None:
                return

            # Propagate the notification to the registered callbacks
            for callback in self._text_open_callbacks:
                callback(opened_file)
        except Exception as e:
            if self._logger is not None:
                self._logger.exception(f"Exception caught during text doc open: {e}")

    def _handle_did_close_text_doc(
        self, notification_context: NotificationContext, params: DidCloseTextDocumentParams
    ) -> None:
        """
        Handles when a file is closed in the workspace.
        The event is propagated to the registered
        file close callbacks
        :param notification_context: Context of the notification
        :param params: Parameters from the notification
        """
        try:
            # Attempt to close the requested file
            if params.text_document is None:
                self._log_warning(f"No text document provided in change: {params}")
                return
            uri = params.text_document.uri
            if uri is None:
                self._log_warning(f"No URI provided in text document change: {params}")
                return
            closed_file: ScriptFile | None = self._workspace.close_file(uri)
            if closed_file is None:
                return

            # Propagate the notification to the registered callbacks
            for callback in self._text_close_callbacks:
                callback(closed_file)
        except Exception as e:
            if self._logger is not None:
                self._logger.exception(f"Exception caught during text doc close: {e}")
