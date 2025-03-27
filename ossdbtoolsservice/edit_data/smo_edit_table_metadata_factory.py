# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.driver import ServerConnection
from ossdbtoolsservice.edit_data import EditColumnMetadata, EditTableMetadata
from ossdbtoolsservice.metadata.contracts.object_metadata import MetadataType, ObjectMetadata
from ossdbtoolsservice.query.contracts import DbColumn
from pgsmo import Server
from pgsmo.objects.table.table import Table
from pgsmo.objects.table_objects.column import Column


class SmoEditTableMetadataFactory:
    def get(
        self,
        connection: ServerConnection,
        schema_name: str,
        object_name: str,
        object_type: str,
    ) -> EditTableMetadata:
        server = Server(connection)

        object_metadata = ObjectMetadata(
            server.urn_base, MetadataType.TABLE, object_type, object_name, schema_name
        )

        result_object: Table | None
        if object_type.lower() == "table":
            result_object = server.find_table(object_metadata)
        elif object_type.lower() == "view":
            result_object = server.find_view(object_metadata)
        else:
            raise ValueError("Not supported object type")

        edit_columns_metadata: list[EditColumnMetadata] = []

        if result_object is not None:
            for column in result_object.columns:
                db_column = self.create_db_column(column)
                edit_columns_metadata.append(
                    EditColumnMetadata(db_column, column.default_value)
                )

        return EditTableMetadata(schema_name, object_name, edit_columns_metadata)

    def create_db_column(self, column: Column) -> DbColumn:
        return DbColumn(
            allow_db_null=column.not_null is False,
            column_name=column.name,
            column_ordinal=column.column_ordinal,
            data_type=column.datatype,
            is_key=column.is_key,
            is_read_only=bool(column.is_readonly),
            is_unique=column.is_unique,
            is_auto_increment=column.is_auto_increment,
            is_updatable=(column.is_readonly is False and column.is_auto_increment is False),
        )
