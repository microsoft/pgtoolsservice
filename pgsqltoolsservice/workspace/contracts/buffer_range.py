# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from buffer_position import BufferPosition


class BufferRange:
    """
    Provides details about a range between two positions in a file buffer
    """

    # CONSTRUCTORS #########################################################
    @classmethod
    def from_position_data(cls, start_line, start_column, end_line, end_column):
        """
        Creates a BufferRange object based on position data
        :param int start_line: 1-based starting line number of the range
        :param int start_column: 1-based starting column number of the range
        :param int end_line: 1-based ending line number of the range
        :param int end_column: 1-based ending column number of the range
        :return BufferRange: BufferRange that starts at start_line:start_column and ends at end_line:end_column
        """
        return cls(BufferPosition(start_line, start_column), BufferPosition(end_line, end_column))

    @classmethod
    def from_positions(cls, start_position, end_position):
        """
        Creates a BufferRange object based on BufferPosition objects
        :param BufferPosition start_position: BufferPosition where the range begins
        :param BufferPosition end_position: BufferPosition where the range ends
        :return BufferRange: BufferRange that starts at start_position and ends at end_position
        """
        return cls(start_position, end_position)

    def __init__(self, start, end):
        """
        Stores the state of a buffer range object, performs basic validation
        :param start: BufferPosition where the range begins
        :param end: BufferPosition where the range ends
        """
        if start > end:
            # TODO: Localize
            raise ValueError("Buffer range cannot have a start position after the end position")

        self._start = start
        self._end = end

    # PROPERTIES ###########################################################
    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value):
        self._start = value

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, value):
        self._end = value

    # METHODS ##############################################################
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        return self.start == other.start and self.end == other.end

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._start) ^ hash(self._end)

    def __str__(self):
        return u"{} to {}".format(self._start, self._end)

# STATIC PROPERTIES ########################################################
BufferRange.none = BufferRange.from_position_data(0, 0, 0, 0)
