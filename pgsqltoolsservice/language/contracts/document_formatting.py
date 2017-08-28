# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds contracts for the language service formatter calls"""

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.workspace.contracts import Range, TextDocumentIdentifier
from pgsqltoolsservice.serialization import Serializable


class FormattingOptions(Serializable):
    """Language Service options passed in each format request"""
    @classmethod
    def from_data(cls, tab_size: int, insert_spaces: bool):
        obj = cls()
        obj.tab_size = tab_size
        obj.insert_spaces = insert_spaces
        return obj

    def __init__(self):
        self.tab_size: int = None
        self.insert_spaces: bool = None


class DocumentFormattingParams(Serializable):
    """
    Parameters used in a formatting request to process an entire document
    """
    @classmethod
    def get_child_serializable_types(cls):
        return {'text_document': TextDocumentIdentifier, 'options': FormattingOptions}

    def __init__(self):
        self.text_document: TextDocumentIdentifier = None
        self.options: FormattingOptions = None


class DocumentRangeFormattingParams(DocumentFormattingParams):
    """
    Parameters used in a formatting request to process a specific text range
    """
    @classmethod
    def get_child_serializable_types(cls):
        return {'range': Range, 'text_document': TextDocumentIdentifier, 'options': FormattingOptions}

    def __init__(self):
        DocumentFormattingParams.__init__(self)
        self.range: Range = None


DOCUMENT_FORMATTING_REQUEST = IncomingMessageConfiguration('textDocument/formatting', DocumentFormattingParams)


DOCUMENT_RANGE_FORMATTING_REQUEST = IncomingMessageConfiguration('textDocument/rangeFormatting', DocumentRangeFormattingParams)
