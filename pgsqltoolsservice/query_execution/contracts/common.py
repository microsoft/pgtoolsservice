# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Contains contracts for query execution service"""

import datetime

import pgsqltoolsservice.utils as utils


class QuerySelection(object):
    """Container class for a selection range from file"""

    @classmethod
    def from_data(cls, start_line: int, start_column: int, end_line: int, end_column: int):
        obj = QuerySelection()
        obj.start_line = start_line
        obj.start_column = start_column
        obj.end_line = end_line
        obj.end_column = end_column

    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.convert_from_dict(cls, dictionary)

    def __init__(self):
        self.start_line: int = 0
        self.start_column: int = 0
        self.end_line: int = 0
        self.end_column: int = 0


class BatchSummary(object):

    def __init__(self, owner_uri, batch_id, selection, execution_start, has_error):
        self.owner_uri = owner_uri
        self.id = batch_id
        self.selection = selection
        self.execution_start = execution_start
        self.has_error = has_error


class ResultMessage(object):

    def __init__(self, owner_uri, message, is_error, batch_id):
        self.owner_uri = owner_uri
        self.message = message
        self.is_error = is_error
        self.batch_id = batch_id
        self.time = datetime.utcnow()


class ResultSetSummary(object):

    def __init__(self, owner_uri, rs_id, row_count):
        self.owner_uri = owner_uri
        self.id = rs_id
        self.row_count = row_count
