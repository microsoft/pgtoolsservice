# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds contracts for the language service formatter calls"""

from typing import Any

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable
from ossdbtoolsservice.workspace.contracts import Range, TextDocumentIdentifier


class FormattingOptions(Serializable):
    """Language Service options passed in each format request"""

    tab_size: int | None
    insert_spaces: bool | None

    @classmethod
    def from_data(cls, tab_size: int, insert_spaces: bool) -> "FormattingOptions":
        obj = cls()
        obj.tab_size = tab_size
        obj.insert_spaces = insert_spaces
        return obj

    def __init__(self) -> None:
        self.tab_size = None
        self.insert_spaces = None


class DocumentFormattingParams(Serializable):
    """
    Parameters used in a formatting request to process an entire document
    """

    text_document: TextDocumentIdentifier | None
    options: FormattingOptions | None

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type[Any]]:
        return {"text_document": TextDocumentIdentifier, "options": FormattingOptions}

    def __init__(self) -> None:
        self.text_document = None
        self.options = None


class DocumentRangeFormattingParams(DocumentFormattingParams):
    """
    Parameters used in a formatting request to process a specific text range
    """

    range: Range | None

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type[Any]]:
        return {
            "range": Range,
            "text_document": TextDocumentIdentifier,
            "options": FormattingOptions,
        }

    def __init__(self) -> None:
        DocumentFormattingParams.__init__(self)
        self.range = None


DOCUMENT_FORMATTING_REQUEST = IncomingMessageConfiguration(
    "textDocument/formatting", DocumentFormattingParams
)


DOCUMENT_RANGE_FORMATTING_REQUEST = IncomingMessageConfiguration(
    "textDocument/rangeFormatting", DocumentRangeFormattingParams
)
