# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import enum
from typing import Any

from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)
from ossdbtoolsservice.serialization import Serializable


class InitializeRequestParams(Serializable):
    """Initialization request parameters"""

    capabilities: Any | None
    initialization_options: Any | None
    process_id: int | None
    trace: str | None
    root_path: str | None
    root_uri: str | None
    workspace_folders: str | None

    def __init__(self) -> None:
        self.capabilities = None  # TODO: Add support for client capabilities
        self.initialization_options = None
        self.process_id = None
        self.trace = None

        # Note: If both root_path and root_uri are available, root_uri is preferred
        self.root_path = None  # Note: Deprecated in favor of root_uri
        self.root_uri = None
        self.workspace_folders = None


class CompletionOptions:
    """Completion options contract"""

    resolve_provider: bool | None
    trigger_characters: list[str] | None

    def __init__(
        self,
        resolve_provider: bool | None = None,
        trigger_characters: list[str] | None = None,
    ) -> None:
        self.resolve_provider = resolve_provider
        self.trigger_characters = trigger_characters


class SignatureHelpOptions:
    """Signature help options contract"""

    trigger_characters: list[str] | None

    def __init__(self, trigger_characters: list[str] | None = None) -> None:
        self.trigger_characters = trigger_characters


class TextDocumentSyncKind(enum.Enum):
    """Text document sync kind contract"""

    NONE = 0
    FULL = 1
    INCREMENTAL = 2


class ServerCapabilities:
    text_document_sync: TextDocumentSyncKind
    hover_provider: bool
    completion_provider: CompletionOptions
    signature_help_provider: SignatureHelpOptions | None
    definition_provider: bool
    references_provider: bool
    document_highlight_provider: bool
    document_formatting_provider: bool
    document_range_formatting_provider: bool
    document_symbol_provider: bool
    workspace_symbol_provider: bool

    def __init__(
        self,
        text_document_sync: TextDocumentSyncKind,
        hover_provider: bool,
        completion_provider: CompletionOptions,
        signature_help_provider: SignatureHelpOptions | None,
        definition_provider: bool,
        references_provider: bool,
        document_highlight_provider: bool,
        document_formatting_provider: bool,
        document_range_formatting_provider: bool,
        document_symbol_provider: bool,
        workspace_symbol_provider: bool,
    ) -> None:
        self.text_document_sync = text_document_sync
        self.hover_provider = hover_provider
        self.completion_provider = completion_provider
        self.signature_help_provider = signature_help_provider
        self.definition_provider = definition_provider
        self.references_provider = references_provider
        self.document_highlight_provider = document_highlight_provider
        self.document_formatting_provider = document_formatting_provider
        self.document_range_formatting_provider = document_range_formatting_provider
        self.document_symbol_provider = document_symbol_provider
        self.workspace_symbol_provider = workspace_symbol_provider


class InitializeResult:
    """Initialization result parameters"""

    capabilities: ServerCapabilities

    def __init__(self, capabilities: ServerCapabilities) -> None:
        self.capabilities: ServerCapabilities = capabilities


INITIALIZE_REQUEST = IncomingMessageConfiguration("initialize", InitializeRequestParams)
OutgoingMessageRegistration.register_outgoing_message(InitializeResult)
OutgoingMessageRegistration.register_outgoing_message(ServerCapabilities)
OutgoingMessageRegistration.register_outgoing_message(TextDocumentSyncKind)
OutgoingMessageRegistration.register_outgoing_message(CompletionOptions)
OutgoingMessageRegistration.register_outgoing_message(SignatureHelpOptions)
