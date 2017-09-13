# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import threading    # noqa
from typing import List, Tuple, Optional
import unittest
from unittest import mock

from tests.utils import MockConnection

class TestConnectedQueue(unittest.TestCase):
    """Methods for testing the ConnectedQueue operation"""

    def setUp(self):
        """Constructor"""
        self.default_connection_key = 'server_db_user'
