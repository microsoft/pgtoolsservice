# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsmo import Server, Schema
from pgsmo.utils.templating import qt_ident
from pgsqltoolsservice.metadata.contracts.object_metadata import ObjectMetadata


class Scripter(object):
    """Service for retrieving operation scripts"""

    def __init__(self, conn):
        # get server from psycopg2 connection
        self.connection = conn
        self.server = Server(conn)

    # SCRIPTING METHODS ############################

    # SELECT ##################################################################

    def script_as_select(self, metadata: ObjectMetadata) -> str:
        """ Function to get script for select operations """
        schema = qt_ident(None, metadata.schema)
        name = qt_ident(None, metadata.name)
        script = f'SELECT *\nFROM {schema}.{name}\nLIMIT 1000\n'
        return script

    # CREATE ##################################################################

    def get_create_script(self, metadata: ObjectMetadata) -> str:
        """ Get create script for all objects """
        try:
            # get object from server
            object_type = metadata.metadata_type_name
            obj = self._get_object(object_type, metadata)

            # get the create script
            script = obj.create_script()

            return script
        except Exception as e:
            # need to handle exceptions well
            return None

    # DELETE ##################################################################
    def get_delete_script(self, metadata: ObjectMetadata) -> str:
        """ Get delete script for all objects """
        try:
            # get object from server
            object_type = metadata.metadata_type_name
            obj = self._get_object(object_type, metadata)

            # get the delete script
            script = obj.delete_script()
            return script
        except Exception:
            return None

    # UPDATE ##################################################################

    def get_update_script(self, metadata: ObjectMetadata) -> str:
        """ Get update script for tables """
        try:
            # get object from server
            object_type = metadata.metadata_type_name
            obj = self._get_object(object_type, metadata)

            # get the update script
            script = obj.update_script()
            return script
        except Exception:
            return None

    # HELPER METHODS ##########################################################

    def _find_schema(self, metadata: ObjectMetadata) -> Schema:
        """ Find the schema in the server to script as """
        schema_name = metadata.name if metadata.metadata_type_name == "Schema" else metadata.schema
        database = self.server.maintenance_db
        parent_schema = None
        try:
            if database.schemas is not None:
                parent_schema = database.schemas[schema_name]
                if parent_schema is not None:
                    return parent_schema

            return None
        except Exception:
            return None

    def _find_table(self, metadata: ObjectMetadata):
        """ Find the table in the server to script as """
        return self._find_schema_child_object('tables', metadata)

    def _find_function(self, metadata: ObjectMetadata):
        """ Find the function in the server to script as """
        return self._find_schema_child_object('functions', metadata)

    def _find_database(self, metadata: ObjectMetadata):
        """ Find a database in the server """
        try:
            database_name = metadata.name
            database = self.server.databases[database_name]
            return database
        except Exception:
            return None

    def _find_view(self, metadata: ObjectMetadata):
        """ Find a view in the server """
        return self._find_schema_child_object('views', metadata)

    def _find_role(self, metadata: ObjectMetadata):
        """ Find a role in the server """
        try:
            role_name = metadata.name
            role = self.server.roles[role_name]
            return role
        except Exception:
            return None

    def _find_sequence(self, metadata: ObjectMetadata):
        """ Find a sequence in the server """
        return self._find_schema_child_object('sequences', metadata)

    def _find_datatype(self, metadata: ObjectMetadata):
        """ Find a datatype in the server """
        return self._find_schema_child_object('datatypes', metadata)

    def _find_schema_child_object(self, prop_name: str, metadata: ObjectMetadata):
        """
        Find an object that is a child of a schema object.
        :param prop_name: name of the property used to query for objects
        of this type on the schema
        :param metadata: metadata including object name and schema name
        """
        try:
            obj_name = metadata.name
            parent_schema = self._find_schema(metadata)
            if not parent_schema:
                return None
            obj_collection = getattr(parent_schema, prop_name)
            if not obj_collection:
                return None
            obj = obj_collection[obj_name]
            return obj
        except Exception:
            return None

    def _get_object(self, object_type: str, metadata: ObjectMetadata):
        """ Retrieve a given object """
        object_map = {
            "Table": self._find_table,
            "Schema": self._find_schema,
            "Database": self._find_database,
            "View": self._find_view,
            "Role": self._find_role,
            "Function": self._find_function,
            "Sequence": self._find_sequence,
            "DataType": self._find_datatype
        }
        return object_map[object_type](metadata)
