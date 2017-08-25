# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.serialization import Serializable


class Position(Serializable):
    """
    Represents a point in the document
    Attributes:
        line:       0-based line number
        character:  0-based column number
    """

    @classmethod
    def from_data(cls, line: int, col: int):
        pos = cls()
        pos.line = line
        pos.character = col
        return pos

    def __init__(self, line=0, character=0):
        self.line: int = line
        self.character: int = character


class Range(Serializable):
    """
    Represents a selection of the document
    Attributes:
        start:  The starting position of the range, inclusive
        end:    The ending position of the range, inclusive
    """

    @classmethod
    def from_data(cls, start_line: int, start_col: int, end_line: int, end_col: int):
        result = cls()
        result.start = Position.from_data(start_line, start_col)
        result.end = Position.from_data(end_line, end_col)
        return result

    @classmethod
    def get_child_serializable_types(cls):
        return {'start': Position, 'end': Position}

    def __init__(self, start=None, end=None):
        self.start: Position = start
        self.end: Position = end


class TextDocumentItem(Serializable):
    """
    Defines a text document
    Attributes:
        uri:            The URI that uniquely identifies the path of the text document
        language_id:    Language of the document
        version:        The version of the document
        text:           Full content of the document
    """

    def __init__(self):
        self.uri: str = None
        self.language_id: str = None
        self.version: int = None
        self.text: str = None


class TextDocumentIdentifier(Serializable):
    """
    Defines a base parameter class for identifying a text document
    Attributes:
        uri:        The URI that uniquely identifies the path of the text document
    """

    def __init__(self):
        self.uri: str = None


class TextDocumentPosition(Serializable):
    """
    Defines a position in a text document
    Attributes:
        text_document: The document identifier
        position: The position in the document
    """

    @classmethod
    def get_child_serializable_types(cls):
        return {'text_document': TextDocumentIdentifier, 'position': Position}

    def __init__(self):
        self.text_document: TextDocumentIdentifier = None
        self.position: Position = None
