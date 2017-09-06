# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import List # noqa

from pgsqltoolsservice.edit_data import EditColumnMetadata
from pgsqltoolsservice.query_execution.contracts.common import DbColumn


class EditTableMetadata():

    def __init__(self, schema_name: str, table_name, columns_metadata: List[EditColumnMetadata]) -> None:
        self.columns_metadata = columns_metadata
        self.schema_name: str = schema_name
        self.table_name: str = table_name
        self.key_columns: List[EditColumnMetadata] = []
        self.has_extended_properties: bool = False

    @property
    def multipart_name(self) -> str:
        return '.'.join([self.schema_name, self.table_name])

    def extend(self, db_columns: List[DbColumn]):

        for index, column in enumerate(db_columns):
            self.columns_metadata[index].extend(column)

        self.key_columns = [column for column in self.columns_metadata if column.is_key is True]

        if any(self.key_columns) is False:
            self.key_columns = [column for column in self.columns_metadata if column.is_trustworthy_for_uniqueness is True]

        self.has_extended_properties = True
