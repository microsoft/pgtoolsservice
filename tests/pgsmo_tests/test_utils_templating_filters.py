# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

import smo.utils.templating as templating


class TestTemplatingFilters(unittest.TestCase):
    # SCAN KEYWORD EXTRA LOOKUP TESTS ######################################
    def test_scan_keyword_extra_lookup_extra(self):
        # If: I scan for a keyword that exists in the extra keywords
        output = templating.scan_keyword_extra_lookup("connect")

        # Then: I should get back the extra keyword info
        self.assertEqual(output, templating._EXTRA_KEYWORDS["connect"])

    def test_scan_keyword_extra_lookup_standard(self):
        # If: I scan for a keyword that exists in the standard keywords
        output = templating.scan_keyword_extra_lookup("abort")

        # Then: I should get back the standard keyword value
        self.assertEqual(output, templating.scan_keyword("abort"))

    def test_scan_keyword_extra_lookup_none(self):
        # If: I scan for a keyword that doesn't exist
        output = templating.scan_keyword_extra_lookup("does_not_exist")

        # Then: I should get back None
        self.assertIsNone(output)

    # NEEDS QUOTING TESTS ##################################################
    # TODO: Add tests that are more based on scenarios and less on code paths
    def test_needs_quoting_int(self):
        # If: An int is provided
        # Then: It should always be quoted
        self.assertTrue(templating.needs_quoting(4, False))
        self.assertTrue(templating.needs_quoting(4, True))

    def test_needs_quoting_type_legal_spaces(self):
        # If: A type is provided that legally has a space in it
        # Then: It shouldn't be quoted
        self.assertFalse(templating.needs_quoting("time with time zone", True))
        self.assertFalse(templating.needs_quoting("time with time zone[]", True))

    def test_needs_quoting_type_already_quoted(self):
        # If: A type is provided that is already quoted
        # Then: It shouldn't be quoted
        self.assertFalse(templating.needs_quoting('"int"', True))

    def test_needs_quoting_numeric_value(self):
        # If: A value is numeric (? starts with 0-9)
        # Then: It should be quoted
        self.assertTrue(templating.needs_quoting("2000", False))

    def test_needs_quoting_non_alphanumeric(self):
        # If: A value is not lowercase alphanumeric
        # Then: It should be quoted
        self.assertTrue(templating.needs_quoting("Something+Else", False))
        self.assertTrue(templating.needs_quoting("Something+Else", True))
