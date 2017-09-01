# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import List # noqa

from pgsmo import Server
from pgsmo.objects.table.table import Table # noqa
from pgsmo.objects.table_objects.column import Column # noqa
from pgsqltoolsservice.edit_data import EditTableMetadata, EditColumnMetadata
from pgsqltoolsservice.utils import object_finder
from pgsqltoolsservice.metadata.contracts.object_metadata import ObjectMetadata
from pgsqltoolsservice.query_execution.contracts.common import DbColumn


class SmoEditTableMetadataFactory:

    def get(self, connection: 'psycopg2.extensions.connection', schema_name: str, object_name: str, object_type: str) -> EditTableMetadata:
        # Check if you can get the object metdata from the client directly

        server = Server(connection)
        result_object: Table = None
        object_metadata = ObjectMetadata.from_data(0, object_type, object_name, schema_name)

        if object_type == 'TABLE':
            result_object = object_finder.find_table(server, object_metadata)
        elif object_type == 'VIEW':
            result_object = object_finder.find_view(server, object_metadata)
        else:
            raise ValueError('Not supported object type')

        edit_columns_metadata: List[EditColumnMetadata] = []

        for column in result_object.columns:
            # Updated
            db_column = self.create_db_column(column)
            edit_column_metadata = EditColumnMetadata()

            edit_column_metadata.is_key = column.is_key
            edit_column_metadata.default_value = column.default_value
            edit_column_metadata.escaped_name = column.name
            edit_column_metadata.ordinal = column.column_ordinal
            edit_column_metadata.db_column = db_column

            edit_columns_metadata.append(edit_column_metadata)

        return EditTableMetadata(schema_name, object_name, edit_columns_metadata)

    def create_db_column(self, column: Column) -> DbColumn:
        db_column = DbColumn()

        db_column.allow_db_null = column.not_null is False
        db_column.column_name = column.name
        db_column.column_ordinal = column.column_ordinal
        db_column.data_type = column.datatype
        db_column.is_key = column.is_key
        db_column.is_read_only = column.is_readonly
        db_column.is_unique = column.is_unique

        return db_column
