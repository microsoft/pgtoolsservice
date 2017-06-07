# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class SelectionData(object):
    def __init__(self, start_line, start_column, end_line, end_column):
        self.StartLine = start_line
        self.StartColumn = start_column
        self.EndLine = end_line
        self.EndColumn = end_column
