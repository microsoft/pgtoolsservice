# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Any

from ossdbtoolsservice.serialization import Serializable


class Position(Serializable):
    """
    Represents a point in the document
    Attributes:
        line:       0-based line number
        character:  0-based column number
    """

    line: int
    character: int

    @classmethod
    def from_data(cls, line: int, col: int) -> "Position":
        pos = cls()
        pos.line = line
        pos.character = col
        return pos

    def __init__(self, line: int = 0, character: int = 0) -> None:
        self.line: int = line
        self.character: int = character


class Range(Serializable):
    """
    Represents a selection of the document
    Attributes:
        start:  The starting position of the range, inclusive
        end:    The ending position of the range, inclusive
    """

    start: Position | None
    end: Position | None

    @classmethod
    def from_data(
        cls, start_line: int, start_col: int, end_line: int, end_col: int
    ) -> "Range":
        result = cls(
            start=Position.from_data(start_line, start_col),
            end=Position.from_data(end_line, end_col),
        )
        return result

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type[Position]]:
        return {"start": Position, "end": Position}

    def __init__(self, start: Position | None = None, end: Position | None = None) -> None:
        self.start = start
        self.end = end


class TextDocumentItem(Serializable):
    """
    Defines a text document
    Attributes:
        uri:            The URI that uniquely identifies the path of the text document
        language_id:    Language of the document
        version:        The version of the document
        text:           Full content of the document
    """

    def __init__(self) -> None:
        self.uri: str | None = None
        self.language_id: str | None = None
        self.version: int | None = None
        self.text: str | None = None


class TextDocumentIdentifier(Serializable):
    """
    Defines a base parameter class for identifying a text document
    Attributes:
        uri:        The URI that uniquely identifies the path of the text document
    """

    uri: str | None

    def __init__(self) -> None:
        self.uri = None


class TextDocumentPosition(Serializable):
    """
    Defines a position in a text document
    Attributes:
        text_document: The document identifier
        position: The position in the document
    """

    text_document: TextDocumentIdentifier | None
    position: Position | None

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type[Any]]:
        return {"text_document": TextDocumentIdentifier, "position": Position}

    def __init__(self) -> None:
        self.text_document = None
        self.position = None

    @classmethod
    def ignore_extra_attributes(cls) -> bool:
        return True


class Location(Serializable):
    """
    Defines a range within a file
    Attributes:
        uri: uri pointing to a file
        range: start and stop position determining range within the file
    """

    uri: str
    range: Range

    def __init__(self, uri: str, rng: Range) -> None:
        self.uri = uri
        self.range = rng
