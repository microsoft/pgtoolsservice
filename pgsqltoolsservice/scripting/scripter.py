# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsmo import Server
from pgsmo.utils.templating import qt_ident
from pgsqltoolsservice.metadata.contracts.object_metadata import ObjectMetadata
from pgsqltoolsservice.utils import object_finder


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
            obj = object_finder.get_object(self.server, object_type, metadata)

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
            obj = object_finder.get_object(self.server, object_type, metadata)

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
            obj = object_finder.get_object(self.server, object_type, metadata)

            # get the update script
            script = obj.update_script()
            return script
        except Exception:
            return None
