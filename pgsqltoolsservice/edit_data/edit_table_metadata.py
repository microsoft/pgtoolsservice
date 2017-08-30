# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import List # noqa

from pgsqltoolsservice.edit_data import EditColumnMetadata
from pgsqltoolsservice.query_execution.contracts.common import DbColumn


class EditTableMetadata():

    def __init__(self, columns_metadata: List[EditColumnMetadata]):
        self.column_metadata = columns_metadata
        self.escaped_multipart_name = None
        self.key_columns: List[EditColumnMetadata] = []

    def extend(self, db_columns: List[DbColumn]):
        # Extend additional properties from the SMO
        pass
