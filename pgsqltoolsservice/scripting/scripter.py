# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsmo.objects.server.server import Server


class Scripter(object):
    """Service for retrieving operation scripts"""

    def __init__(self, conn):
        # get server from psycopg2 connection
        self.connection = conn
        self.server = Server(conn)

    # SCRIPTING METHODS ############################

    # SELECT ##################################################################

    def script_as_select(self, metadata) -> str:
        """ Function to get script for select operations """
        schema = metadata["schema"]
        name = metadata["name"]
        # wrap quotes only around objects with all small letters
        name = f'"{name}"' if name.islower() else name
        script = f"SELECT *\nFROM {schema}.{name}\nLIMIT 1000\n"
        return script

    # CREATE ##################################################################

    def get_create_script(self, metadata) -> str:
        """ Get create script for all objects """
        try:
            # get object from server
            object_type = metadata["metadataTypeName"]
            obj = self._get_object(object_type, metadata)

            # get the create script
            script = obj.create_script(self.connection)

            return script
        except Exception:
            # need to handle exceptions well
            return None

    # DELETE ##################################################################
    def get_delete_script(self, metadata) -> str:
        """ Get delete script for all objects """
        try:
            # get object from server
            object_type = metadata["metadataTypeName"]
            obj = self._get_object(object_type, metadata)

            # get the delete script
            script = obj.delete_script(self.connection)
            return script
        except Exception:
            return None

    # UPDATE ##################################################################

    def get_update_script(self, metadata) -> str:
        """ Get update script for tables """
        try:
            # get object from server
            object_type = metadata["metadataTypeName"]
            obj = self._get_object(object_type, metadata)

            # get the update script
            script = obj.update_script(self.connection)
            return script
        except Exception:
            return None

    # HELPER METHODS ##########################################################

    def _find_schema(self, metadata):
        """ Find the schema in the server to script as """
        table_schema = metadata["schema"]
        databases = self.server.databases
        parent_schema = None
        try:
            for db in databases:
                parent_schema = db.schemas[table_schema]
                return parent_schema
        except Exception:
            return None

    def _find_table(self, metadata):
        """ Find the table in the server to script as """
        try:
            table_name = metadata["name"]
            parent_schema = self._find_schema(metadata)
            for table in parent_schema.tables:
                return parent_schema.tables[table_name]
        except Exception:
            return None

    def _find_function(self, metadata):
        """ Find the function in the server to script as """
        try:
            function_name = metadata["name"]
            parent_schema = self._find_schema(metadata)
            return parent_schema.functions[function_name]
        except Exception:
            return None

    def _find_database(self, metadata):
        """ Find a database in the server """
        try:
            database_name = metadata["name"]
            database = self.server.databases[database_name]
            return database
        except Exception:
            return None

    def _find_view(self, metadata):
        """ Find a view in the server """
        try:
            view_name = metadata["name"]
            parent_schema = self._find_schema(metadata)
            view = parent_schema.views[view_name]
            return view
        except Exception:
            return None

    def _find_role(self, metadata):
        """ Find a role in the server """
        try:
            role_name = metadata["name"]
            role = self.server.roles[role_name]
            return role
        except Exception:
            return None

    def _get_object(self, object_type: str, metadata):
        """ Retrieve a given object """
        object_map = {
            "Table": self._find_table,
            "Schema": self._find_schema,
            "Database": self._find_database,
            "View": self._find_view,
            "Role": self._find_role,
            "Function": self._find_function
        }
        return object_map[object_type](metadata)
