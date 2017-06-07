# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.workspace.contracts.common import TextDocumentItem
import pgsqltoolsservice.utils as utils


class DidCloseTextDocumentParams:
    """
    Parameters to receive with a textDocument/didClose notification
    Attributes:
        text_document:  The document that was closed
    """

    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.deserialize_from_dict(cls, dictionary,
                                           text_document=TextDocumentItem)

    def __init__(self):
        self.text_document: TextDocumentItem = None


DID_CLOSE_TEXT_DOCUMENT_NOTIFICATION = IncomingMessageConfiguration(
    'textDocument/didClose',
    DidCloseTextDocumentParams
)
