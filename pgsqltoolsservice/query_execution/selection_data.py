# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class SelectionData(object):
    def __init__(self, start_line: int, start_column: int, end_line: int, end_column: int):
        """Constructs a SelectionData object"""
        self.startLine: int = start_line
        self.startColumn: int = start_column
        self.endLine: int = end_line
        self.endColumn: int = end_column
