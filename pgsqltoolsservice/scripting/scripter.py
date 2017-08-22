# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsmo.objects.server.server import Server
from pgsqltoolsservice.utils import object_finder


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
        schema = metadata.schema
        name = metadata.name
        # wrap quotes only around objects with all small letters
        name = f'"{name}"' if name.islower() else name
        script = f"SELECT *\nFROM {schema}.{name}\nLIMIT 1000\n"
        return script

    # CREATE ##################################################################

    def get_create_script(self, metadata) -> str:
        """ Get create script for all objects """
        try:
            # get object from server
            object_type = metadata.metadata_type_name
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
            object_type = metadata.metadata_type_name
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
            object_type = metadata.metadata_type_name
            obj = self._get_object(object_type, metadata)

            # get the update script
            script = obj.update_script(self.connection)
            return script
        except Exception:
            return None

    # HELPER METHODS ##########################################################

    def _get_object(self, object_type: str, metadata):
        """ Retrieve a given object """
        object_map = {
            "Table": object_finder.find_table,
            "Schema": object_finder.find_schema,
            "Database": object_finder.find_database,
            "View": object_finder.find_view,
            "Role": object_finder.find_role,
            "Function": object_finder.find_function
        }
        return object_map[object_type](self.server, metadata)
