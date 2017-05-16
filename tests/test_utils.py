# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test server.py"""

import json
import unittest

from pgsqltoolsservice.contracts.initialization import (
    CompletionOptions,
    ServerCapabilities,
    TextDocumentSyncKind
)
from pgsqltoolsservice.utils import get_serializable_value


class TestConnectionService(unittest.TestCase):
    """Methods for testing utility functions"""

    def test_get_serializable_value(self):
        """Test that the get_serializable_value function can be used to covert objects to JSON"""
        test_object = ServerCapabilities(
            textDocumentSync=TextDocumentSyncKind.FULL,
            referencesProvider=True,
            completionProvider=CompletionOptions(
                resolveProvider=None,
                triggerCharacters=None
            )
        )
        # Verify that the object cannot be serialized. If it ever can, the test
        # should be updated
        with self.assertRaises(TypeError):
            json.dumps(test_object)
        # Verify that the object can be serialized when using the utility
        # function
        result = json.dumps(test_object, default=get_serializable_value)
        self.assertIsNotNone(result)
        # Verify that the result represents the object
        result_dict = json.loads(result)
        self.assertEqual(
            result_dict['textDocumentSync'],
            TextDocumentSyncKind.FULL.value)
        self.assertTrue(result_dict['referencesProvider'])
        self.assertTrue('resolveProvider' in result_dict['completionProvider'])


if __name__ == '__main__':
    unittest.main()
