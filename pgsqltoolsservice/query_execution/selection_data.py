# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class SelectionData(object):    

        def __init__(self, start_line, start_column, end_line, end_column):
                """Constructs a SelectionData object"""
                self.startLine = start_line
                self.startColumn = start_column
                self.endLine = end_line
                self.endColumn = end_column
