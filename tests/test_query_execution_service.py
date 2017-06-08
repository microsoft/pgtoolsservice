# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test connection.ConnectionService"""

from __future__ import unicode_literals

import unittest
from unittest.mock import Mock

import psycopg2

from pgsqltoolsservice.connection.contracts.contract_impl import CONNECTION_COMPLETE_NOTIFICATION_TYPE, ConnectionType
from pgsqltoolsservice.query_execution.query_execution_service import QueryExecutionService
from pgsqltoolsservice.server import Server


class TestQueryService(unittest.TestCase):
    """Methods for testing the connection service"""

    def test_connect(self):
        query_execution_service = QueryExecutionService(None)

if __name__ == '__main__':
    unittest.main()
