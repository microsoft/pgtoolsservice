# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class BufferPosition:
    """
    Provides details about a position in a file buffer. All positions are expressed in 1-based positions (ie, the
    first line and column in the file is position 1,1)
    """

    def __init__(self, line, column):
        """
        Initializes internal state of a buffer position
        :param line: The 1-indexed line number of the buffer position
        :param column: The 1-indexed column number of the buffer position
        """
        self._column = column
        self._line = line

    # PROPERTIES ###########################################################
    @property
    def column(self):
        return self._column

    @column.setter
    def column(self, value):
        self._column = value

    @property
    def line(self):
        return self._line

    @line.setter
    def line(self, value):
        self._line = value

    # METHODS ##############################################################
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        return self.column == other.column and self.line == other.line

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        return (self.line > other.line) or (self.line == other.line and self.column > other.column)

    def __lt__(self, other):
        return other > self

    def __hash__(self):
        return hash(self._line) ^ hash(self._column)

    def __str__(self):
        return u"{}:{}".format(self._line, self._column)
