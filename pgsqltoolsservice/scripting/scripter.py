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

    def get_database_create_script(self, metadata) -> str:
        """ Get create script for databases """
        try:
            # get database from server
            database_name = metadata["name"]
            database = self.server.databases[database_name]

            # get the create script
            script = database.create_script(self.connection)
            return script
        except Exception:
            # need to handle exceptions well
            return None

    def get_view_create_script(self, metadata) -> str:
        """ Get create script for views """
        try:
            # get view from server
            view_name = metadata["name"]
            parent_schema = self._find_schema(metadata)
            view = parent_schema.views[view_name]

            # get the create script
            script = view.create_script(self.connection)
            return script
        except Exception:
            return None

    def get_table_create_script(self, metadata) -> str:
        """ Get create script for tables """
        try:
            # get table from server
            table = self._find_table(metadata)

            # get the create script
            script = table.create_script(self.connection)
            return script
        except Exception:
            return None

    def get_schema_create_script(self, metadata) -> str:
        """ Get create script for schema """
        try:
            # get schema from server
            schema = self._find_schema(metadata)

            # get the create script
            script = schema.create_script(self.connection)
            return script
        except Exception:
            return None

    def get_role_create_script(self, metadata) -> str:
        """ Get create script for role """
        try:
            # get roles from server
            role_name = metadata["name"]
            role = self.server.roles[role_name]

            # get the create script
            script = role.create_script(self.connection)
            return script
        except:
            return None

    # DELETE ##################################################################
    def get_table_delete_script(self, metadata) -> str:
        """ Get delete script for table """
        try:
            table = self._find_table(metadata)
            script = table.delete_script(self.connection)
            return script
        except Exception:
            return None

    def get_view_delete_script(self, metadata) -> str:
        """ Get delete script for view """
        try:
            # get view from server
            view_name = metadata["name"]
            parent_schema = self._find_schema(metadata)
            view = parent_schema.views[view_name]

            # get the delete script
            script = view.delete_script(self.connection)
            return script
        except Exception:
            return None

    def get_database_delete_script(self, metadata) -> str:
        """ Get delete script for databases """
        try:
            # get database from server
            database_name = metadata["name"]
            database = self.server.databases[database_name]

            # get the delete script
            script = database.delete_script(self.connection)
            return script
        except Exception:
            return None

    def get_schema_delete_script(self, metadata) -> str:
        """ Get delete script for schemas """
        try:
            # get schema from server
            schema = self._find_schema(metadata)

            # get the delete script
            script = schema.delete_script(self.connection)
            return script
        except Exception:
            return None

    # UPDATE ##################################################################

    def get_table_update_script(self, metadata) -> str:
        """ Get update script for tables """
        try:
            # get table from server
            table = self._find_table(metadata)

            # get the create script
            script = table.update_script(self.connection)
            return script
        except Exception:
            return None

    def get_view_update_script(self, metadata) -> str:
        """ Get update date script for view """
        try:
            # get view from server
            view_name = metadata["name"]
            parent_schema = self._find_schema(metadata)
            view = parent_schema.views[view_name]

            # get the create script
            script = view.update_script(self.connection)
            return script
        except Exception:
            return None

    def get_schema_update_script(self, metadata) -> str:
        """ Get update script for schemas """
        try:
            # get schema from server
            schema = self._find_schema(metadata)

            # get the delete script
            script = schema.update_script(self.connection)
            return script
        except Exception:
            return None

    def get_role_update_script(self, metadata) -> str:
        """ Get update script for roles """
        try:
            # get roles from server
            role_name = metadata["name"]
            role = self.server.roles[role_name]

            # get the create script
            script = role.update_script(self.connection)
            return script
        except:
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
