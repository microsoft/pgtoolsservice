# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

import pgsmo.utils as pgsmo_utils


class TestTemplatingFilters(unittest.TestCase):
    # SCAN KEYWORD EXTRA LOOKUP TESTS ######################################
    def test_scan_keyword_extra_lookup_extra(self):
        # If: I scan for a keyword that exists in the extra keywords
        output = pgsmo_utils.templating.ScanKeywordExtraLookup('connect')

        # Then: I should get back the extra keyword info
        self.assertEqual(output, pgsmo_utils.templating._EXTRA_KEYWORDS['connect'])

    def test_scan_keyword_extra_lookup_standard(self):
        # If: I scan for a keyword that exists in the standard keywords
        output = pgsmo_utils.templating.ScanKeywordExtraLookup('abort')

        # Then: I should get back the standard keyword value
        self.assertEqual(output, pgsmo_utils.templating._KEYWORD_DICT['abort'])

    def test_scan_keyword_extra_lookup_none(self):
        # If: I scan for a keyword that doesn't exist
        output = pgsmo_utils.templating.ScanKeywordExtraLookup('does_not_exist')

        # Then: I should get back None
        self.assertIsNone(output)

    # QTLITERAL TESTS ######################################################
    def test_qtliteral_no_encoding(self):
        # If: I provide a value that doesn't have an encoding
        output = pgsmo_utils.templating.qtLiteral(4)

        # Then: I should get a quoted literal back
        self.assertEqual(output, '4')

    def test_qtliteral_bytes(self):
        # If: I provide a byte array
        output = pgsmo_utils.templating.qtLiteral(b'123')

        # Then: I should get the byte array decoded as UTF-8 back
        self.assertEqual(output, "'123'::bytea")

    def test_qtliteral_string(self):
        # If: I provide a string
        output = pgsmo_utils.templating.qtLiteral("123")

        # Then: I should get the quoted string back
        self.assertEqual(output, "'123'")

    # NEEDS QUOTING TESTS ##################################################
    # TODO: Add tests that are more based on scenarios and less on code paths
    def test_needs_quoting_int(self):
        # If: An int is provided
        # Then: It should always be quoted
        self.assertTrue(pgsmo_utils.templating.needsQuoting(4, False))
        self.assertTrue(pgsmo_utils.templating.needsQuoting(4, True))

    def test_needs_quoting_type_legal_spaces(self):
        # If: A type is provided that legally has a space in it
        # Then: It shouldn't be quoted
        self.assertFalse(pgsmo_utils.templating.needsQuoting('time with time zone', True))
        self.assertFalse(pgsmo_utils.templating.needsQuoting('time with time zone[]', True))

    def test_needs_quoting_type_already_quoted(self):
        # If: A type is provided that is already quoted
        # Then: It shouldn't be quoted
        self.assertFalse(pgsmo_utils.templating.needsQuoting('"int"', True))

    def test_needs_quoting_numeric_value(self):
        # If: A value is numeric (? starts with 0-9)
        # Then: It should be quoted
        self.assertTrue(pgsmo_utils.templating.needsQuoting('2000', False))

    def test_needs_quoting_non_alphanumeric(self):
        # If: A value is not lowercase alphanumeric
        # Then: It should be quoted
        self.assertTrue(pgsmo_utils.templating.needsQuoting('Something+Else', False))
        self.assertTrue(pgsmo_utils.templating.needsQuoting('Something+Else', True))

