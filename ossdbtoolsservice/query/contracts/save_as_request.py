# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.serialization import Serializable


class SaveResultsRequestParams(Serializable):

    def __init__(self):
        self.file_path: str = None
        self.batch_index: int = None
        self.result_set_index: int = None
        self.owner_uri: str = None
        self.row_start_index: int = None
        self.row_end_index: int = None
        self.column_start_index: int = None
        self.column_end_index: int = None

    @property
    def is_save_selection(self) -> bool:
        return (
            self.row_start_index is not None and self.row_end_index is not None
            and self.column_start_index is not None and self.column_end_index is not None
        )

    @classmethod
    def ignore_extra_attributes(cls):
        return True
