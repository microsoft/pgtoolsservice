# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from ostoolsservice.language.completion.packages.parseutils.meta import FunctionMetadata


class TestFunctionMetadata(unittest.TestCase):
    """Methods for testing CTE Processing"""

    def test_function_metadata_eq(self):
        f1 = FunctionMetadata(
            's', 'f', ['x'], ['integer'], [], 'int', False, False, False, None
        )
        f2 = FunctionMetadata(
            's', 'f', ['x'], ['integer'], [], 'int', False, False, False, None
        )
        f3 = FunctionMetadata(
            's', 'g', ['x'], ['integer'], [], 'int', False, False, False, None
        )
        # Testing operators, so will only use assert_true for checks
        self.assertTrue(f1 == f2)
        self.assertTrue(f1 != f3)
        self.assertTrue(not (f1 != f2))
        self.assertTrue(not (f1 == f3))
        self.assertTrue(hash(f1) == hash(f2))
        self.assertTrue(hash(f1) != hash(f3))
