# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils


class SimpleExecuteRequest:
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self):
        self.owner_uri: str = None
        self.query_string: str = None


SIMPLE_EXECUTE_REQUEST = IncomingMessageConfiguration('query/simpleexecute', SimpleExecuteRequest)


class SimpleExecuteResponse:

    def __init__(self, rows, row_count: int, column_info):
        self.rows = rows
        self.row_count = row_count
        self.column_info = column_info
