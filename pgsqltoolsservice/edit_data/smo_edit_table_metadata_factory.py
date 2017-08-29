# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import List # noqa

from pgsmo import Server
from pgsmo.objects.table.table import Table # noqa
from pgsqltoolsservice.edit_data import EditTableMetadata, EditColumnMetadata
from pgsqltoolsservice.utils import object_finder
from pgsqltoolsservice.metadata.contracts.object_metadata import ObjectMetadata


class SmoEditTableMetadataFactory:

    def get(self, connection: 'psycopg2.extensions.connection', schema_name: str, object_name: str, object_type: str) -> EditTableMetadata:
        # Check if you can get the object metdata from the client directly

        server = Server(connection)
        result_object: Table = None
        object_metadata = ObjectMetadata.from_data(0, object_type, object_name, schema_name)

        if object_type == 'Table':
            result_object = object_finder.find_table(server, object_metadata)
        elif object_type == 'View':
            result_object = object_finder.find_view(server, object_metadata)
        else:
            raise ValueError('Not supported object type')

        edit_columns_metadata: List[EditColumnMetadata] = []

        for column in result_object.columns:
            # Need to populate all the required column attributes
            edit_column_metadata = EditColumnMetadata()
            edit_columns_metadata.append(edit_column_metadata)

        return EditTableMetadata(edit_columns_metadata)
