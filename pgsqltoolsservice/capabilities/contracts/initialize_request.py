# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import enum

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.serialization import Serializable


class InitializeRequestParams(Serializable):
    """Initialization request parameters"""

    def __init__(self):
        self.capabilities: any = None    # TODO: Add support for client capabilities
        self.initialization_options: any = None
        self.process_id: int = None
        self.trace: str = None

        # Note: If both root_path and root_uri are available, root_uri is preferred
        self.root_path: str = None      # Note: Deprecated in favor of root_uri
        self.root_uri: str = None


class CompletionOptions:
    """Completion options contract"""

    def __init__(self, resolve_provider=None, trigger_characters=None):
        self.resolve_provider = resolve_provider
        self.trigger_characters = trigger_characters


class SignatureHelpOptions:
    """Signature help options contract"""

    def __init__(self, trigger_characters=None):
        self.trigger_characters = trigger_characters


class TextDocumentSyncKind(enum.Enum):
    """Text document sync kind contract"""
    NONE = 0
    FULL = 1
    INCREMENTAL = 2


class ServerCapabilities:
    def __init__(self,
                 text_document_sync=None,
                 hover_provider=None,
                 completion_provider=None,
                 signature_help_provider=None,
                 definition_provider=None,
                 references_provider=None,
                 document_highlight_provider=None,
                 document_formatting_provider=None,
                 document_range_formatting_provider=None,
                 document_symbol_provider=None,
                 workspace_symbol_provider=None):
        self.text_document_sync: TextDocumentSyncKind = text_document_sync
        self.hover_provider: bool = hover_provider
        self.completion_provider: CompletionOptions = completion_provider
        self.signature_help_provider: SignatureHelpOptions = signature_help_provider
        self.definition_provider: bool = definition_provider
        self.references_provider: bool = references_provider
        self.document_highlight_provider: bool = document_highlight_provider
        self.document_formatting_provider: bool = document_formatting_provider
        self.document_range_formatting_provider: bool = document_range_formatting_provider
        self.document_symbol_provider: bool = document_symbol_provider
        self.workspace_symbol_provider: bool = workspace_symbol_provider


class InitializeResult:
    """Initialization result parameters"""

    def __init__(self, capabilities: ServerCapabilities):
        self.capabilities: ServerCapabilities = capabilities


INITIALIZE_REQUEST = IncomingMessageConfiguration('initialize', InitializeRequestParams)
