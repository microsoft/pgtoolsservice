# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Contains contract classes for the connection service"""

from enum import Enum

CONNECTION_COMPLETE_NOTIFICATION_TYPE = 'connection/complete'


class ConnectionType(Enum):
    """
    String constants that represent connection types.

    Default: Connection used by the editor. Opened by the editor upon the initial connection.
    Query: Connection used for executing queries. Opened when the first query is executed.
    """
    DEFAULT = 'Default'
    QUERY = 'Query'
    EDIT = 'Edit'


class ConnectionCompleteParams(object):
    """Parameters to be sent back with a connection complete event"""

    def __init__(self, ownerUri=None, connectionId=None, messages=None, errorMessage=None, errorNumber=0,
                 serverInfo=None, connectionSummary=None, type=ConnectionType.DEFAULT):
        self.ownerUri = ownerUri
        self.connectionId = connectionId
        self.messages = messages
        self.errorMessage = errorMessage
        self.errorNumber = errorNumber
        self.serverInfo = serverInfo
        self.connectionSummary = connectionSummary
        self.type = type


class ConnectionSummary(object):
    """Provides high level information about a connection"""

    def __init__(self, serverName=None, databaseName=None, userName=None):
        self.serverName = serverName
        self.databaseName = databaseName
        self.userName = userName
