# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.query.contracts import DbCellValue


class EditCell(DbCellValue):
    is_dirty: bool

    @classmethod
    def from_db_cell_value(
        cls, db_cell_value: DbCellValue, is_dirty: bool, row_id: int | None = None
    ) -> "EditCell":
        return cls(
            display_value=db_cell_value.display_value,
            is_null=db_cell_value.is_null,
            row_id=row_id or db_cell_value.row_id,
            raw_object=db_cell_value.raw_object,
            is_dirty=is_dirty,
        )
