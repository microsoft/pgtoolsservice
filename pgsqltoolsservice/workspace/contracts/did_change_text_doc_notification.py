# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional     # noqa

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.workspace.contracts.common import Range
from pgsqltoolsservice.serialization import Serializable


class TextDocumentChangeEvent(Serializable):
    """
    Represents a change in the text of the document.
    Attributes:
        range:          Range where the document was changed. Will be null if the server's
                        TextDocumentSyncKind is Full
        range_length:   Length of the range being replaced in the document. Will be null if the
                        server's TextDocumentSyncKind is Full
        text:           The new text for the document
    """
    @classmethod
    def get_child_serializable_types(cls):
        return {'range': Range}

    def __init__(self):
        self.range: Optional[Range] = None
        self.range_length: Optional[int] = None
        self.text: str = None


class VersionedTextDocumentIdentifier(Serializable):
    """
    Define a specific version of a text document
    Attributes:
        version:    Version of the changed text document
        uri:        The URI that uniquely identifies the path of the text document
    """
    def __init__(self):
        self.version: int = None
        self.uri: str = None


class DidChangeTextDocumentParams(Serializable):
    """
    Parameters for a testDocument/didChange notification
    Attributes:
        content_changes:    List of changes to the document's contents
        text_document:      The document that changed
    """
    @classmethod
    def get_child_serializable_types(cls):
        return {'content_changes': TextDocumentChangeEvent, 'text_document': VersionedTextDocumentIdentifier}

    def __init__(self):
        self.content_changes: List[TextDocumentChangeEvent] = []
        self.text_document: VersionedTextDocumentIdentifier = None


DID_CHANGE_TEXT_DOCUMENT_NOTIFICATION = IncomingMessageConfiguration(
    'textDocument/didChange',
    DidChangeTextDocumentParams
)
