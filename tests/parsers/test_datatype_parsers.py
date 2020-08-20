# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import datetime  # noqa
import unittest
import uuid
from decimal import Decimal
from typing import Callable  # noqa

from ossdbtoolsservice.parsers.datatype_parsers import get_parser
from ossdbtoolsservice.utils.constants import (MYSQL_PROVIDER_NAME,
                                               PG_PROVIDER_NAME)


class TestPGDataTypeParsers(unittest.TestCase):

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

    def test_date_parser(self):
        date = '2017/12/12'
        parsed_value: datetime.date = self._get_parsed_value('date', date)

        self.assertEqual(12, parsed_value.day)
        self.assertEqual(12, parsed_value.month)
        self.assertEqual(2017, parsed_value.year)

    def test_time_parser(self):
        time = '12:30:42'
        parsed_value: datetime.time = self._get_parsed_value('time', time)

        self.assertEqual(12, parsed_value.hour)
        self.assertEqual(30, parsed_value.minute)
        self.assertEqual(42, parsed_value.second)

    def test_time_with_timezone_parser(self):
        time = '12:30:42+12:1'
        parsed_value: datetime.time = self._get_parsed_value('timetz', time)

        self.assertEqual(12, parsed_value.hour)
        self.assertEqual(30, parsed_value.minute)
        self.assertEqual(42, parsed_value.second)

        self.assertIsNotNone(parsed_value.tzinfo)

    def _test_parsers_for(self, datatype_to_test: str, value_to_parse: str, expected_type: type, expected_parsed_value: object):
        parsed_value = self._get_parsed_value(datatype_to_test, value_to_parse)

        self.assertEqual(type(parsed_value), expected_type)
        self.assertEqual(parsed_value, expected_parsed_value)

    def _get_parsed_value(self, datatype_to_test: str, value_to_parse: str):
        parser = get_parser(datatype_to_test, PG_PROVIDER_NAME)

        return parser(value_to_parse)

class TestMySQLDataTypeParsers(unittest.TestCase):

    def test_float_parser(self):
        self._test_parsers_for('float', '0', float, float(0))
        self._test_parsers_for('double', '0', float, float(0))

    def test_int_parser(self):
        self._test_parsers_for('tinyint', '2', int, int(2))
        self._test_parsers_for('smallint', '3', int, int(3))
        self._test_parsers_for('mediumint', '4', int, int(4))
        self._test_parsers_for('int', '4', int, int(4))
        self._test_parsers_for('bigint', '4', int, int(4))

    def test_number_parser(self):
        self._test_parsers_for('numeric', '0', Decimal, Decimal(0))
        self._test_parsers_for('decimal', '0', Decimal, Decimal(0))

    def test_varchar_text_char_parser(self):
        text = 'Some Text Ϣ'
        self._test_parsers_for('varchar', text, str, str(text))
        self._test_parsers_for('text', text, str, str(text))
        self._test_parsers_for('char', 'c', str, str('c'))

    def test_date_parser(self):
        date = '2017-12-12'
        parsed_value: datetime.date = self._get_parsed_value('date', date)

        self.assertEqual(12, parsed_value.day)
        self.assertEqual(12, parsed_value.month)
        self.assertEqual(2017, parsed_value.year)

    def test_time_parser(self):
        time = '12:30:42'
        parsed_value: datetime.time = self._get_parsed_value('time', time)

        self.assertEqual(12, parsed_value.hour)
        self.assertEqual(30, parsed_value.minute)
        self.assertEqual(42, parsed_value.second)

    def test_timestamp(self):
        time = '2017-12-12 12:30:42'
        parsed_value: datetime.time = self._get_parsed_value('timestamp', time)

        self.assertEqual(12, parsed_value.day)
        self.assertEqual(12, parsed_value.month)
        self.assertEqual(2017, parsed_value.year)

        self.assertEqual(12, parsed_value.hour)
        self.assertEqual(30, parsed_value.minute)
        self.assertEqual(42, parsed_value.second)
    
    def test_datetime(self):
        time = '2017-12-12 12:30:42'
        parsed_value: datetime.time = self._get_parsed_value('datetime', time)

        self.assertEqual(12, parsed_value.day)
        self.assertEqual(12, parsed_value.month)
        self.assertEqual(2017, parsed_value.year)

        self.assertEqual(12, parsed_value.hour)
        self.assertEqual(30, parsed_value.minute)
        self.assertEqual(42, parsed_value.second)

    def _test_parsers_for(self, datatype_to_test: str, value_to_parse: str, expected_type: type, expected_parsed_value: object):
        parsed_value = self._get_parsed_value(datatype_to_test, value_to_parse)

        self.assertEqual(type(parsed_value), expected_type)
        self.assertEqual(parsed_value, expected_parsed_value)

    def _get_parsed_value(self, datatype_to_test: str, value_to_parse: str):
        parser = get_parser(datatype_to_test, MYSQL_PROVIDER_NAME)

        return parser(value_to_parse)

if __name__ == '__main__':
    unittest.main()
