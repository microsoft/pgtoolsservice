# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.serialization import Serializable


class SaveResultsRequestParams(Serializable):
    file_path: str | None
    batch_index: int | None
    result_set_index: int | None
    owner_uri: str | None
    row_start_index: int | None
    row_end_index: int | None
    column_start_index: int | None
    column_end_index: int | None

    def __init__(self) -> None:
        self.file_path = None
        self.batch_index = None
        self.result_set_index = None
        self.owner_uri = None
        self.row_start_index = None
        self.row_end_index = None
        self.column_start_index = None
        self.column_end_index = None

    @property
    def is_save_selection(self) -> bool:
        return (
            self.row_start_index is not None
            and self.row_end_index is not None
            and self.column_start_index is not None
            and self.column_end_index is not None
        )

    @classmethod
    def ignore_extra_attributes(cls) -> bool:
        return True
