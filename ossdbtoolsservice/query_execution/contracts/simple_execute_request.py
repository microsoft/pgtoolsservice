# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)
from ossdbtoolsservice.query.contracts import DbCellValue, DbColumn
from ossdbtoolsservice.serialization import Serializable


class SimpleExecuteRequest(Serializable):
    owner_uri: str | None
    query_string: str | None

    def __init__(self, owner_uri: str | None = None, query_string: str | None = None) -> None:
        self.owner_uri = None
        self.query_string = None


class SimpleExecuteResponse(Serializable):
    rows: list[list[DbCellValue]]
    row_count: int
    column_info: list[DbColumn]

    def __init__(
        self, rows: list[list[DbCellValue]], row_count: int, column_info: list[DbColumn]
    ) -> None:
        self.rows = rows
        self.row_count = row_count
        self.column_info = column_info


SIMPLE_EXECUTE_REQUEST_METHOD = "query/simpleexecute"
SIMPLE_EXECUTE_REQUEST = IncomingMessageConfiguration(
    SIMPLE_EXECUTE_REQUEST_METHOD, SimpleExecuteRequest
)
OutgoingMessageRegistration.register_outgoing_message(SimpleExecuteResponse)
