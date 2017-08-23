# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Tests the scripter module"""
import unittest

from pgsqltoolsservice.metadata.contracts.object_metadata import ObjectMetadata
from pgsqltoolsservice.scripting.scripter import Scripter

import tests.utils as utils


class TestScripter(unittest.TestCase):
    """Methods for testing the scripter module"""

    def setUp(self):
        """Set up mock objects for testing the scripting service.
        Ran before each unit test.
        """
        self.scripter = Scripter(utils.MockConnection({"port": "8080", "host": "test", "dbname": "test"}))
        self.server = self.scripter.server

    # TESTS ################################################################

    def test_script_select_escapes_non_lowercased_words(self):
        """ Tests scripting for select operations"""
        # Given mixed, and uppercase object names
        # When I generate a select script
        mixed_result: str = self.scripter.script_as_select(ObjectMetadata.from_data(0, 'Table', 'MyTable', 'MySchema'))
        upper_result: str = self.scripter.script_as_select(ObjectMetadata.from_data(0, 'Table', 'MYTABLE', 'MYSCHEMA'))

        # Then I expect words to be escaped no matter what
        self.assertTrue('"MySchema"."MyTable"' in mixed_result)
        self.assertTrue('"MYSCHEMA"."MYTABLE"' in upper_result)

        # Given lowercase object names
        # When I generate a select script
        lower_result: str = self.scripter.script_as_select(ObjectMetadata.from_data(0, 'Table', 'mytable', 'myschema'))
        # Then I expect words to be left as-is
        self.assertTrue('myschema.mytable' in lower_result)
