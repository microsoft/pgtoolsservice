# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import enum


class ConnectionSummary(object):
    """Provides high level information about a connection"""

    def __init__(self):
        self.server_name: str = None
        self.database_name: str = None
        self.user_name: str = None


class ConnectionType(enum.Enum):
    """
    String constants that represent connection types.

    Default: Connection used by the editor. Opened by the editor upon the initial connection.
    Query: Connection used for executing queries. Opened when the first query is executed.
    """
    DEFAULT = 'Default'
    QUERY = 'Query'
    EDIT = 'Edit'
