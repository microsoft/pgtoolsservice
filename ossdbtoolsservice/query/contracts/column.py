# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Any

from psycopg import Column

import ossdbtoolsservice.parsers.datatypes as datatypes
from ossdbtoolsservice.core.models import PGTSBaseModel
from ossdbtoolsservice.hosting import OutgoingMessageRegistration
from ossdbtoolsservice.utils import constants

DESC = {
    "name": 0,
    "type_code": 1,
    "display_size": 2,
    "internal_size": 3,
    "precision": 4,
    "scale": 5,
    "null_ok": 6,
}

CHARS_DATA_TYPES = [
    datatypes.DATATYPE_TEXT,
    datatypes.DATATYPE_VARCHAR,
    datatypes.DATATYPE_JSON,
    datatypes.DATATYPE_JSONB,
]

SYSTEM_DATA_TYPES = [
    value for key, value in datatypes.__dict__.items() if key.startswith("DATATYPE")
]


def get_column_name(column_index: int, column_name: str) -> str:
    if column_name == "?column?":
        return f"Column{column_index + 1}"

    return column_name


class DbColumn(PGTSBaseModel):
    allow_db_null: bool | None = None
    base_catalog_name: str | None = None
    column_size: int | None = None
    numeric_precision: int | None = None
    numeric_scale: int | None = None
    base_schema_name: str | None = None
    base_server_name: str | None = None
    base_table_name: str | None = None
    column_ordinal: int | None = None
    base_column_name: str | None = None
    column_name: str | None = None
    is_aliased: bool | None = None
    is_auto_increment: bool | None = None
    is_expression: bool | None = None
    is_hidden: bool | None = None
    is_identity: bool | None = None
    is_key: bool | None = None
    is_read_only: bool = False
    is_unique: bool | None = None
    data_type: str | None = None
    is_updatable: bool = False

    @property
    def is_chars(self) -> bool:
        return self.data_type in CHARS_DATA_TYPES

    @property
    def is_xml(self) -> bool:
        return self.data_type == datatypes.DATATYPE_XML

    @property
    def is_bytes(self) -> bool:
        return self.data_type == datatypes.DATATYPE_BYTEA

    @property
    def is_long(self) -> bool:
        return self.is_chars or self.is_xml or self.is_bytes or self.is_udt or self.is_json

    @property
    def is_udt(self) -> bool:
        return self.data_type not in SYSTEM_DATA_TYPES

    @property
    def is_json(self) -> bool:
        return (
            self.data_type == datatypes.DATATYPE_JSON
            or self.data_type == datatypes.DATATYPE_JSONB
        )

    @property
    def provider(self) -> str:
        return constants.PG_PROVIDER_NAME

    @provider.setter
    def provider(self, name: str) -> None:
        self._provider = name

    # The cursor_description is an element from psycopg's cursor class' description property.
    # It is a property that is a tuple (read-only) containing a 7-item sequence.
    # Each inner sequence item can be referenced by using DESC
    @classmethod
    def from_cursor_description(
        cls, column_ordinal: int, cursor_description: Column
    ) -> "DbColumn":
        column_name = get_column_name(column_ordinal, cursor_description[DESC["name"]])
        return cls(
            # Note that 'null_ok' is always 'None' by default because it's
            # not easy to retrieve
            # Need to take a look if we should turn this on if it's important
            allow_db_null=cursor_description[DESC["null_ok"]],
            base_column_name=column_name,
            column_name=column_name,
            data_type=cursor_description.type_display,
            # From documentation, it seems like 'internal_size' is for the max size and
            # 'display_size' is for the actual size based off of the
            # largest entry in the column so far.
            # 'display_size' is always 'None' by default since it's expensive to calculate.
            # 'internal_size' is negative if column max is of a dynamic / variable size
            column_size=cursor_description[DESC["internal_size"]],
            numeric_precision=cursor_description[DESC["precision"]],
            numeric_scale=cursor_description[DESC["scale"]],
            column_ordinal=column_ordinal,
        )


class DbCellValue:
    display_value: str
    is_null: bool
    row_id: int | None
    raw_object: Any

    def __init__(
        self, display_value: Any, is_null: bool, raw_object: Any, row_id: int | None
    ) -> None:
        self.display_value: str = "" if (display_value is None) else str(display_value)
        self.is_null: bool = is_null
        self.row_id = row_id
        self.raw_object = raw_object


OutgoingMessageRegistration.register_outgoing_message(DbColumn)
OutgoingMessageRegistration.register_outgoing_message(DbCellValue)
