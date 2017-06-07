# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils
import pgsqltoolsservice.workspace.contracts.common as common


class VersionedTextDocumentIdentifier:
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.deserialize_from_dict(cls, dictionary)

    def __init__(self):
        self.version: int = None
        self.uri: str = None


class TextDocumentChangeEvent:
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.deserialize_from_dict(cls, dictionary,
                                           range=common.BufferRange)

    def __init__(self):
        self.range: [common.BufferRange, None] = None
        self.range_length: [int, None] = None
        self.text: str = None

    def as_file_change(self) -> common.FileChange:
        # The protocol's positions are 0-based, so add 1 to all offsets
        obj = common.FileChange()


class DidChangeTextDocumentParams:
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.deserialize_from_dict(cls, dictionary,
                                           text_document=VersionedTextDocumentIdentifier,
                                           content_changes=TextDocumentChangeEvent)

    def __init__(self):
        self.text_document: VersionedTextDocumentIdentifier = None
        self.content_changes: List[TextDocumentChangeEvent] = None


DID_CHANGE_TEXT_DOCUMENT_NOTIFICATION = IncomingMessageConfiguration(
    'textDocument/didChange',
    DidChangeTextDocumentParams
)
