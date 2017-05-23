# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class FileChange:
    """
    Contains details relating to a content change in an open file
    
    :ivar string insert_string: The string which is to be inserted in the file 
    :ivar line:             The 1-based line number where the change starts
    :ivar offset:           The 1-based column offset where the change starts
    :ivar end_line:         The 1-based line number where the change ends
    :ivar end_offset        The 1-based column offset where the change ends
    """

    @classmethod
    def from_dict(cls, json_dict):
        file_change = cls()
        file_change.insert_string = json_dict['InsertString']
        file_change.line = json_dict['Line']
        file_change.offset = json_dict['Offset']
        file_change.end_line = json_dict['EndLine']
        file_change.end_offset = json_dict['EndOffset']
        return file_change

    def __init__(self):
        self.insert_string = None
        self.line = None
        self.offset = None
        self.end_line = None
        self.end_offset = None
