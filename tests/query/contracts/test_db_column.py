# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

import ossdbtoolsservice.parsers.mysql_datatypes as datatypes
from ossdbtoolsservice.query.contracts import DbColumn


class TestDbColumn(unittest.TestCase):

    def test_is_chars_with_type_text(self):
        self.validate_evaluated_properties('is_chars', datatypes.DATATYPE_TEXT, self.assertTrue)

    def test_is_chars_with_type_varchar(self):
        self.validate_evaluated_properties('is_chars', datatypes.DATATYPE_VARCHAR, self.assertTrue)

    def test_is_chars_with_type_json(self):
        self.validate_evaluated_properties('is_chars', datatypes.DATATYPE_JSON, self.assertTrue)

    def test_is_chars_with_type_other(self):
        self.validate_evaluated_properties('is_chars', datatypes.DATATYPE_BIGINT, self.assertFalse)

    def test_is_json_with_type_other(self):
        self.validate_evaluated_properties('is_json', datatypes.DATATYPE_BIGINT, self.assertFalse)

    def test_is_json_with_type_json(self):
        self.validate_evaluated_properties('is_json', datatypes.DATATYPE_JSON, self.assertTrue)

    def test_is_long_with_type_text(self):
        self.validate_evaluated_properties('is_long', datatypes.DATATYPE_TEXT, self.assertTrue)

    def test_is_long_with_type_json(self):
        self.validate_evaluated_properties('is_long', datatypes.DATATYPE_JSON, self.assertTrue)

    def test_is_long_with_type_utd(self):
        self.validate_evaluated_properties('is_long', 'User_Defined_Type', self.assertTrue)

    def test_is_udt_with_type_other_than_defined(self):
        self.validate_evaluated_properties('is_udt', 'User_Defined_Type', self.assertTrue)

    def validate_evaluated_properties(self, assertion_property, data_type: str, assertion):
        column = DbColumn()
        column.data_type = data_type

        assertion(getattr(column, assertion_property))


if __name__ == '__main__':
    unittest.main()
