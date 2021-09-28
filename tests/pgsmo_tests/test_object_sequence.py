# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock
from pgsmo import Sequence
import tests.pgsmo_tests.utils as utils
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase

from pgsmo.objects.server.server import Server


class TestSequence(NodeObjectTestBase, unittest.TestCase):
    NODE_ROW = {
        'name': 'sequencename',
        'oid': 123,
        'schema': 'public',
        'schemaoid': 456,
        'objectname': 'sequencename',
        'is_system': True
    }

    @property
    def class_for_test(self):
        return Sequence

    @property
    def basic_properties(self):
        return {}

    @property
    def collections(self):
        return []

    @property
    def node_query(self) -> dict:
        return TestSequence.NODE_ROW

    @property
    def full_properties(self):
        return {
            "name": "name",
            "seqowner": "seqowner",
            "comment": "comment",
            "acl": "acl",
            "securities": "securities"
        }

    @property
    def property_query(self) -> dict:
        return {
            "name": "test",
            "schema": "public",
            "seqowner": None,
            "comment": None,
            "acl": None,
            "securities": None
        }
    
    @property
    def full_properties(self):
        return {
            "cycled": "cycled",
            "increment": "increment",
            "start": "start",
            "current_value": "current_value",
            "minimum": "minimum",
            "maximum": "maximum",
            "cache": "cache",
            "cascade": "cascade"
        }

    @property
    def property_query(self) -> dict:
        return {
            "schema": "public",
            "cycled": False,
            "increment": 1,
            "start": 1,
            "current_value": None,
            "minimum": 1,
            "maximum": 100,
            "cache": 1,
            "cascade": None
        }

