# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

import pgsmo.utils.urn as urn


class TestUtilsUrn(unittest.TestCase):
    def test_process_urn_invalid(self):
        # Create test cases of invalid URNs
        test_cases = [
            '',                 # Nothing
            '/',                # No components
            'Database.123/',    # Missing leading slash
            '/.123/'            # Missing class name
            '/12d345.123/',     # Numeric class name
            '/Database123/',    # Missing separator .
            '/Database./',      # Missing OID
            '/Database.abc/',   # Alpha OID
            '/Database.123',    # Missing trailing slash,
            'A Bunch Of Garbage'
        ]

        for case in test_cases:
            with self.assertRaises(ValueError):
                # If: I process a URN that's invalid
                # Then: I should get an exception
                urn.process_urn(case)

    def test_process_urn_success(self):
        # Create test cases of valid URNs
        test_cases = [
            ('Database', 123, '/'),
            ('Database', 123, '/Schema.456/'),
            ('Database', 123, '/Schema.456/Table.789/')
        ]

        for case in test_cases:
            # If: I process a valid URN
            full_urn = f'/{case[0]}.{case[1]}{case[2]}'
            klass, oid, fragment = urn.process_urn(full_urn)

            # Then: The components should match the input components
            self.assertEqual(klass, case[0])
            self.assertEqual(oid, case[1])
            self.assertEqual(fragment, case[2])
