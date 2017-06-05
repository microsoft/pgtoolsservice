# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils


class DidCloseTextDocumentParams:
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.deserialize_from_dict(cls, dictionary,
                                           text_document=TextDocumentItem)

    def __init__(self):
        self.text_document: TextDocumentItem = None


did_close_text_document_notification = IncomingMessageConfiguration(
    'textDocument/didClose',
    DidCloseTextDocumentParams
)
