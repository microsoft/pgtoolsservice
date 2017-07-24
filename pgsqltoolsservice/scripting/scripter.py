# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import pgsmo.utils.querying as querying
from pgsmo.objects.server.server import Server


class Scripter(object):
    """Service for retrieving operation scripts"""
    def __init__(self, conn: querying.ServerConnection):
        # retrieve psycopg2 connection to get server
        self.connection = conn
        self.server = Server(conn.connection)

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
        except:
            return None

    def _find_table(self, metadata):
        """ Find the table in the server to script as """
        try:
            table_name = metadata["name"]
            parent_schema = self._find_schema(metadata)
            for table in parent_schema.tables:
                return parent_schema.tables[table_name]
        except:
            return None

    ############################ SCRIPTING METHODS ############################
    
    # CREATE ##################################################################

    def get_database_create_script(self, metadata) -> str:
        """ Get create script for databases """
        try:
            # get database from server
            database_name = metadata["name"]
            database = self.server.databases[database_name]

            # get the create script
            script = database.create(self.connection)
            return script
        except:
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
            script = view.create(self.connection)
            return script
        except: 
            return None

    def get_table_create_script(self, metadata) -> str:
        """ Get create script for tables """
        try:
            # get table from server
            table = self._find_table(metadata)

            # get the create script
            script = table.create(self.connection)
            return script
        except: 
            return None

    # SELECT #################################################################

    def get_table_select_script(self, metadata) -> str:
        """ Get select script for tables """
        return 

    def get_database_select_script(self, metadata) -> str:
        """ Get select script for databases """
        return

    def get_view_select_script(self, metadata) -> str:
        """ Get select script for views """
        return

    # INSERT ##################################################################
    def get_table_insert_script(self, metadata) -> str:
        """ Get insert script for table """
        return 

    def get_view_insert_script(self, metadata) -> str:
        """ Get insert script for view """
        return 

    def get_database_insert_script(self, metadata) -> str:
        """ Get insert script for databases """
        return