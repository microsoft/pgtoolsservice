# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import pgsqltoolsservice.utils as utils


class Position:
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

    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self):
        self.line: int = 0
        self.character: int = 0

    def __eq__(self, other) -> bool:
        if other is None or not isinstance(other, Position):
            return False

        return self.line == other.line and self.character == other.character

    def __ne__(self, other) -> bool:
        return not self == other

    def __hash__(self) -> int:
        hash_code: int = 17
        hash_code = hash_code * 23 + hash(self.line)
        hash_code = hash_code * 23 + hash(self.character)
        return hash_code

    def __str__(self) -> str:
        return 'Position = {}:{}'.format(self.line, self.character)


class Range:
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
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary,
                                                     start=Position,
                                                     end=Position)

    def __init__(self):
        self.start: Position = None
        self.end: Position = None

    def __eq__(self, other) -> bool:
        if other is None or not isinstance(other, Range):
            return False

        return self.start == other.start and self.end == other.end

    def __ne__(self, other) -> bool:
        return not self == other

    def __hash__(self) -> int:
        hash_code: int = 17
        hash_code = hash_code * 23 + hash(self.start)
        hash_code = hash_code * 23 + hash(self.end)
        return hash_code

    def __str__(self) -> str:
        return 'Start = {}:{}, End = {}:{}'.format(self.start.line, self.start.character,
                                                   self.end.line, self.end.character)


class TextDocumentItem:
    """
    Defines a text document
    Attributes:
        uri:            The URI that uniquely identifies the path of the text document
        language_id:    Language of the document
        version:        The version of the document
        text:           Full content of the document
    """

    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self):
        self.uri: str = None
        self.language_id: str = None
        self.version: int = None
        self.text: str = None
