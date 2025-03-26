# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable
from ossdbtoolsservice.workspace.contracts.common import TextDocumentItem


class DidCloseTextDocumentParams(Serializable):
    """
    Parameters to receive with a textDocument/didClose notification
    Attributes:
        text_document:  The document that was closed
    """

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type[TextDocumentItem]]:
        return {"text_document": TextDocumentItem}

    def __init__(self) -> None:
        self.text_document: TextDocumentItem | None = None


DID_CLOSE_TEXT_DOCUMENT_NOTIFICATION = IncomingMessageConfiguration(
    "textDocument/didClose", DidCloseTextDocumentParams
)
