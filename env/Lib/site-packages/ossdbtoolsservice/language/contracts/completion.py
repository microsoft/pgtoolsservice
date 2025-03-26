# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds contracts for the completion service calls"""

import enum
from typing import Any

from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)
from ossdbtoolsservice.language.contracts import TextEdit  # noqa
from ossdbtoolsservice.serialization import Serializable
from ossdbtoolsservice.workspace.contracts import TextDocumentPosition


class CompletionItemKind(enum.Enum):
    """
    The kind of a completion entry. These are defined by the
    Language Service specification. SQL types are loosely mapped to these.
    """

    Text = 1
    Method = 2
    Function = 3
    Constructor = 4
    Field = 5
    Variable = 6
    Class = 7
    Interface = 8
    Module = 9
    Property = 10
    Unit = 11
    Value = 12
    Enum = 13
    Keyword = 14
    Snippet = 15
    Color = 16
    File = 17
    Reference = 18


class CompletionItem(Serializable):
    """
    Completion items are presented in an IntelliSense user interface, representing valid
    items to complete an in-process typing
    """

    label: str | None
    kind: CompletionItemKind | None
    detail: str | None
    documentation: str | None
    sort_text: str | None
    filter_text: str | None
    insert_text_format: str | None
    text_edit: TextEdit | None
    data: Any | None

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type[Any]]:
        return {"kind": CompletionItemKind, "text_edit": TextEdit}

    def __init__(self) -> None:
        self.label = None
        self.kind = None
        self.detail = None
        self.documentation = None
        self.sort_text = None
        self.filter_text = None
        self.insert_text_format = None
        self.text_edit = None
        self.data = None


COMPLETION_REQUEST = IncomingMessageConfiguration(
    "textDocument/completion", TextDocumentPosition
)

COMPLETION_RESOLVE_REQUEST = IncomingMessageConfiguration(
    "completionItem/resolve", CompletionItem
)
OutgoingMessageRegistration.register_outgoing_message(CompletionItem)
