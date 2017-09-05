# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import unittest
from typing import Callable # noqa
from decimal import Decimal
import uuid

from pgsqltoolsservice.parsers.datatype_parsers import get_parser
from pgsqltoolsservice.query_execution.contracts.common import DbColumn


class TestDataTypeParsers(unittest.TestCase):

    def test_boolean_parser_for_true(self):

        self._test_parsers_for('bool', '1', bool, True)
        self._test_parsers_for('bool', 'y', bool, True)
        self._test_parsers_for('bool', 'yes', bool, True)
        self._test_parsers_for('bool', 't', bool, True)
        self._test_parsers_for('bool', 'trUE', bool, True)
        self._test_parsers_for('bool', 'true', bool, True)
        self._test_parsers_for('bool', 'TRUE', bool, True)

    def test_boolean_parser_for_false(self):
        self._test_parsers_for('bool', '0', bool, False)
        self._test_parsers_for('bool', 'n', bool, False)
        self._test_parsers_for('bool', 'no', bool, False)
        self._test_parsers_for('bool', 'f', bool, False)
        self._test_parsers_for('bool', 'FaLsE', bool, False)
        self._test_parsers_for('bool', 'false', bool, False)
        self._test_parsers_for('bool', 'FALSE', bool, False)

    def test_float_parser(self):
        self._test_parsers_for('float4', '0', float, float(0))

    def test_int_parser(self):
        self._test_parsers_for('int2', '2', int, int(2))
        self._test_parsers_for('int4', '3', int, int(3))
        self._test_parsers_for('int8', '4', int, int(4))

    def test_number_parser(self):
        self._test_parsers_for('numeric', '0', Decimal, Decimal(0))

    def test_varchar_text_char_parser(self):
        text = 'Some Text Ϣ'
        self._test_parsers_for('varchar', text, str, str(text))
        self._test_parsers_for('text', text, str, str(text))
        self._test_parsers_for('char', 'c', str, str('c'))

    def test_uuid_parser(self):
        id = uuid.uuid4()
        self._test_parsers_for('uuid', str(id), uuid.UUID, id)

    def _test_parsers_for(self, datatype_to_test: str, value_to_parse: str, expected_type: type, expected_parsed_value: object):

        column = DbColumn()
        column.data_type = datatype_to_test

        parser = get_parser(column)

        parsed_value = parser(value_to_parse)

        self.assertEqual(type(parsed_value), expected_type)
        self.assertEqual(parsed_value, expected_parsed_value)


if __name__ == '__main__':
    unittest.main()
