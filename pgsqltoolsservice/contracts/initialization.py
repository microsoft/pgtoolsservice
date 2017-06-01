# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# TODO: Move these classes into the capabilities service

"""Contains contract classes for service initialization"""

import enum


class InitializeResult(object):
    """Initialization result contract"""

    def __init__(self, capabilities=None):
        self.capabilities = capabilities


class ServerCapabilities(object):
    """Server capabilities contract"""

    def __init__(
            self,
            textDocumentSync=None,
            hoverProvider=None,
            completionProvider=None,
            signatureHelpProvider=None,
            definitionProvider=None,
            referencesProvider=None,
            documentHighlightProvider=None,
            documentFormattingProvider=None,
            documentRangeFormattingProvider=None,
            documentSymbolProvider=None,
            workspaceSymbolProvider=None):
        self.textDocumentSync = textDocumentSync
        self.hoverProvider = hoverProvider
        self.completionProvider = completionProvider
        self.signatureHelpProvider = signatureHelpProvider
        self.definitionProvider = definitionProvider
        self.referencesProvider = referencesProvider
        self.documentHighlightProvider = documentHighlightProvider
        self.documentFormattingProvider = documentFormattingProvider
        self.documentRangeFormattingProvider = documentRangeFormattingProvider
        self.documentSymbolProvider = documentSymbolProvider
        self.workspaceSymbolProvider = workspaceSymbolProvider


class TextDocumentSyncKind(enum.Enum):
    """Text document sync kind contract"""
    NONE = 0
    FULL = 1
    INCREMENTAL = 2


class CompletionOptions(object):
    """Completion options contract"""

    def __init__(self, resolveProvider=None, triggerCharacters=None):
        self.resolveProvider = resolveProvider
        self.triggerCharacters = triggerCharacters


class SignatureHelpOptions(object):
    """Signature help options contract"""

    def __init__(self, triggerCharacters=None):
        self.triggerCharacters = triggerCharacters
