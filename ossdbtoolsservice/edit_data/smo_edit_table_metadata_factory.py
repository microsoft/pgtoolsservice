# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import List  # noqa

from pgsmo import Server
from pgsmo.objects.table.table import Table  # noqa
from pgsmo.objects.table_objects.column import Column  # noqa
from ossdbtoolsservice.driver import ServerConnection
from ossdbtoolsservice.edit_data import EditTableMetadata, EditColumnMetadata
from ossdbtoolsservice.metadata.contracts.object_metadata import ObjectMetadata
from ossdbtoolsservice.query.contracts import DbColumn


class SmoEditTableMetadataFactory:

    def get(self, connection: ServerConnection, schema_name: str, object_name: str, object_type: str) -> EditTableMetadata:

        server = Server(connection)
        result_object: Table = None
        object_metadata = ObjectMetadata(server.urn_base, None, object_type, object_name, schema_name)

        if object_type.lower() == 'table':
            result_object = server.find_table(object_metadata)
        elif object_type.lower() == 'view':
            result_object = server.find_view(object_metadata)
        else:
            raise ValueError('Not supported object type')

        edit_columns_metadata: List[EditColumnMetadata] = []

        for column in result_object.columns:
            db_column = self.create_db_column(column)
            edit_columns_metadata.append(EditColumnMetadata(db_column, column.default_value))

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
        db_column.is_auto_increment = column.is_auto_increment
        db_column.is_updatable = column.is_readonly is False and column.is_auto_increment is False

        return db_column
