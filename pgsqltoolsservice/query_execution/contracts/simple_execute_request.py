# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils
from pgsqltoolsservice.query_execution.contracts.common import DbColumn, DbCellValue


class SimpleExecuteRequest:
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self):
        self.owner_uri: str = None
        self.query_string: str = None


class SimpleExecuteResponse:

    def __init__(self, rows: List[List[DbCellValue]], row_count: int, column_info: List[DbColumn]):
        self.rows = rows
        self.row_count = row_count
        self.column_info = column_info


SIMPLE_EXECUTE_REQUEST = IncomingMessageConfiguration('query/simpleexecute', SimpleExecuteRequest)
