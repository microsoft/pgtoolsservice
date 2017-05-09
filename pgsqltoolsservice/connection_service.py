# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds the connection service class, which allows for the user to connect and
disconnect and holds the current connection, if one is present"""

import psycopg2


class ConnectionService(object):
    """Manage a single connection, including the ability to connect/disconnect"""

    def __init__(self):
        self.connection = None

    def connect(self, connectionstring):
        """
        Open a connection using the given connection string.

        If a connection was already open, disconnect first. Return whether the connection was
        successful
        """
        if self.connection:
            self.disconnect()
        try:
            self.connection = psycopg2.connect(connectionstring)
            return True
        except Exception:
            return False

    def disconnect(self):
        """Close a connection, if there is currently one open"""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                return False
            self.connection = None

        return True
