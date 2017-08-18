# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test utils.py"""

import enum
import unittest

import pgsqltoolsservice.utils as utils


class TestUtils(unittest.TestCase):
    """Methods for testing utility functions"""

    def test_convert_to_dict(self):
        """
        Test that the convert_to_dict function creates the proper dictionary representation of a complex object

        The object includes nested objects, lists containing objects, dicts containing objects, and enums
        """
        test_object = _ConversionTestClass()
        converted_dict = utils.serialization.convert_to_dict(test_object)
        self.assertEqual(converted_dict, test_object.expected_dict())

    def test_convert_from_dict(self):
        """
        Test that the convert_from_dict function creates the proper object representation of a complex object
        """
        test_object = _ConversionTestClass()
        json_to_convert = test_object.expected_dict()
        result = _ConversionTestClass.from_dict(json_to_convert)
        self.assertEqual(result.test_int, test_object.test_int)
        self.assertEqual(result.nested_object.test_int, test_object.nested_object.test_int)
        self.assertEqual(result.nested_object.test_string, test_object.nested_object.test_string)
        self.assertGreater(len(result.list), 0)
        list_result = result.list[0]
        self.assertEqual(list_result.test_int, test_object.list[0].test_int)
        self.assertEqual(list_result.test_string, test_object.list[0].test_string)
        for key in test_object.dict:
            self.assertIn(key, result.dict)  # TODO: Update once dicts are converted correctly
        self.assertEqual(len(test_object.dict), len(result.dict))
        self.assertEqual(result.enum, test_object.enum)


class _ConversionTestClass:
    """Test class to be used for testing dictionary conversions"""

    @classmethod
    def from_dict(cls, dictionary: dict):
        """from_dict method intended to be similar to the one used in contract classes"""
        return utils.serialization.convert_from_dict(cls, dictionary, nested_object=_NestedTestClass,
                                                     list=_NestedTestClass, enum=_TestEnum)

    def __init__(self):
        self.test_int = 1
        self.nested_object = _NestedTestClass()
        self.list = [_NestedTestClass()]
        self.dict = {'test_key': _NestedTestClass()}
        self.enum = _TestEnum.SECOND_OPTION

    def expected_dict(self):
        """The expected dictionary representation of the instance, for comparison with the utility function output"""
        return {
            'testInt': self.test_int,
            'nestedObject': self.nested_object.expected_dict(),
            'list': [self.nested_object.expected_dict()],
            'dict': {
                'test_key': self.nested_object.expected_dict()
            },
            'enum': self.enum.value
        }


class _NestedTestClass:
    """Test class to be nested within other classes to ensure recursive conversion works"""

    @classmethod
    def from_dict(cls, dictionary: dict):
        """from_dict method intended to be similar to the one used in contract classes"""
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self):
        self.test_int = 1
        self.test_string = 'test_string'

    def expected_dict(self):
        """The expected dictionary representation of the instance, for comparison with the utility function output"""
        return {
            'testInt': self.test_int,
            'testString': self.test_string
        }


class _TestEnum(enum.Enum):
    """Test enum to be included in the _ConversionTestClass to ensure enum conversion works"""
    FIRST_OPTION = 1
    SECOND_OPTION = 2


if __name__ == '__main__':
    unittest.main()
