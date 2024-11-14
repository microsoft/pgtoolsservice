# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds contracts for the completion service calls"""

import enum

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.workspace.contracts import TextDocumentPosition
from ossdbtoolsservice.language.contracts import TextEdit   # noqa
from ossdbtoolsservice.serialization import Serializable


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
    label: str
    kind: CompletionItemKind
    detail: str
    documentation: str
    sort_text: str
    filter_text: str
    insert_text_format: str
    text_edit: TextEdit
    data: any

    @classmethod
    def get_child_serializable_types(cls):
        return {'kind': CompletionItemKind, 'text_edit': TextEdit}

    def __init__(self):
        self.label: str = None
        self.kind: CompletionItemKind = None
        self.detail: str = None
        self.documentation: str = None
        self.sort_text: str = None
        self.filter_text: str = None
        self.insert_text_format: str = None
        self.text_edit: TextEdit = None
        self.data: any = None


COMPLETION_REQUEST = IncomingMessageConfiguration('textDocument/completion', TextDocumentPosition)

COMPLETION_RESOLVE_REQUEST = IncomingMessageConfiguration('completionItem/resolve', CompletionItem)
