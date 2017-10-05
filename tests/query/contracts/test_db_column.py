# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

import pgsqltoolsservice.parsers.datatypes as DT
from pgsqltoolsservice.query.contracts import DbColumn


class TestDbColumn(unittest.TestCase):

    def test_is_chars_with_type_text(self):
        self.validate_evaluated_properties('is_chars', DT.DATATYPE_TEXT, self.assertTrue)

    def test_is_chars_with_type_varchar(self):
        self.validate_evaluated_properties('is_chars', DT.DATATYPE_VARCHAR, self.assertTrue)

    def test_is_chars_with_type_json(self):
        self.validate_evaluated_properties('is_chars', DT.DATATYPE_JSON, self.assertTrue)

    def test_is_chars_with_type_other(self):
        self.validate_evaluated_properties('is_chars', DT.DATATYPE_BIGINT, self.assertFalse)

    def test_is_xml_with_type_other(self):
        self.validate_evaluated_properties('is_xml', DT.DATATYPE_BIGINT, self.assertFalse)

    def test_is_xml_with_type_xml(self):
        self.validate_evaluated_properties('is_xml', DT.DATATYPE_XML, self.assertTrue)

    def test_is_bytes_with_type_other(self):
        self.validate_evaluated_properties('is_bytes', DT.DATATYPE_BIGINT, self.assertFalse)

    def test_is_bytes_with_type_bytea(self):
        self.validate_evaluated_properties('is_bytes', DT.DATATYPE_BYTEA, self.assertTrue)

    def test_is_json_with_type_other(self):
        self.validate_evaluated_properties('is_json', DT.DATATYPE_BIGINT, self.assertFalse)

    def test_is_json_with_type_json(self):
        self.validate_evaluated_properties('is_json', DT.DATATYPE_JSON, self.assertTrue)

    def test_is_long_with_type_text(self):
        self.validate_evaluated_properties('is_long', DT.DATATYPE_TEXT, self.assertTrue)

    def test_is_long_with_type_xml(self):
        self.validate_evaluated_properties('is_long', DT.DATATYPE_XML, self.assertTrue)

    def test_is_long_with_type_bytea(self):
        self.validate_evaluated_properties('is_long', DT.DATATYPE_BYTEA, self.assertTrue)

    def test_is_long_with_type_json(self):
        self.validate_evaluated_properties('is_long', DT.DATATYPE_JSON, self.assertTrue)

    def test_is_long_with_type_utd(self):
        self.validate_evaluated_properties('is_long', 'User_Defined_Type', self.assertTrue)

    def test_is_long_with_type_others(self):
        self.validate_evaluated_properties('is_long', DT.DATATYPE_BOOL, self.assertFalse)

    def test_is_udt_with_type_other_than_defined(self):
        self.validate_evaluated_properties('is_udt', 'User_Defined_Type', self.assertTrue)

    def validate_evaluated_properties(self, assertion_property, data_type: str, assertion):
        column = DbColumn()
        column.data_type = data_type

        assertion(getattr(column, assertion_property))


if __name__ == '__main__':
    unittest.main()
