# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.query.contracts import DbColumn


class EditColumnMetadata:
    def __init__(self, db_column: DbColumn, default_value: str) -> None:
        self.db_column: DbColumn = db_column
        self.default_value = default_value

    @property
    def ordinal(self) -> int | None:
        return self.db_column.column_ordinal

    @property
    def name(self) -> str | None:
        return self.db_column.column_name

    @property
    def is_key(self) -> bool | None:
        return self.db_column.is_key

    @property
    def is_trustworthy_for_uniqueness(self) -> bool:
        return bool(self.db_column.is_unique) or bool(self.db_column.is_auto_increment)

    @property
    def is_calculated(self) -> bool:
        return bool(self.db_column.is_auto_increment) or not self.db_column.is_updatable
