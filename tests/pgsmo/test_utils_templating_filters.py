# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path as path
import unittest
import unittest.mock as mock

import jinja2

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
