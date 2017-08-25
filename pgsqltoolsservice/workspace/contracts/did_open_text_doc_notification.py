# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.workspace.contracts.common import TextDocumentItem
from pgsqltoolsservice.serialization import Serializable


class DidOpenTextDocumentParams(Serializable):
    """
    Parameters for a textDocument/didOpen notification
    Attributes:
        text_document:  The document that was opened
    """
    @classmethod
    def get_child_serializable_types(cls):
        return {'text_document': TextDocumentItem}

    def __init__(self):
        self.text_document: TextDocumentItem = None


DID_OPEN_TEXT_DOCUMENT_NOTIFICATION = IncomingMessageConfiguration(
    'textDocument/didOpen',
    DidOpenTextDocumentParams
)
