# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from ossdbtoolsservice.hosting.json_message import JSONRPCMessage, JSONRPCMessageType


class JsonRpcMessageTests(unittest.TestCase):
    def test_create_error(self):
        # If: I create an error message
        message = JSONRPCMessage.create_error(10, 20, "msg", {})

        # Then:
        # ... The message should have all the properties I defined
        self.assertIsNotNone(message)
        self.assertEqual(message.message_id, 10)
        self.assertIsNone(message.message_method)
        self.assertIsNone(message.message_params)
        self.assertIsNone(message.message_result)
        self.assertIsNotNone(message.message_error)
        self.assertEqual(message.message_error["code"], 20)
        self.assertEqual(message.message_error["message"], "msg")
        self.assertDictEqual(message.message_error["data"], {})
        self.assertEqual(message.message_type, JSONRPCMessageType.ResponseError)

        # ... The dictionary should have the same values stored
        dictionary = message.dictionary
        self.assertIsNotNone(dictionary)
        self.assertDictEqual(
            dictionary,
            {"jsonrpc": "2.0", "error": {"code": 20, "message": "msg", "data": {}}, "id": 10},
        )

    def test_create_response(self):
        # If: I create a response
        message = JSONRPCMessage.create_response(10, {})

        # Then:
        # ... The message should have all the properties I defined
        self.assertIsNotNone(message)
        self.assertEqual(message.message_id, 10)
        self.assertIsNone(message.message_method)
        self.assertIsNone(message.message_params)
        self.assertIsNotNone(message.message_result)
        self.assertDictEqual(message.message_result, {})
        self.assertIsNone(message.message_error)
        self.assertEqual(message.message_type, JSONRPCMessageType.ResponseSuccess)

        # ... The dictionary should have the same values stored
        dictionary = message.dictionary
        self.assertIsNotNone(dictionary)
        self.assertDictEqual(dictionary, {"jsonrpc": "2.0", "result": {}, "id": 10})

    def test_create_request(self):
        # If: I create a request
        message = JSONRPCMessage.create_request(10, "test/test", {})

        # Then:
        # ... The message should have all the properties I defined
        self.assertIsNotNone(message)
        self.assertEqual(message.message_id, 10)
        self.assertEqual(message.message_method, "test/test")
        self.assertDictEqual(message.message_params, {})
        self.assertIsNone(message.message_result)
        self.assertIsNone(message.message_error)
        self.assertEqual(message.message_type, JSONRPCMessageType.Request)

        # ... The dictionary should have the same values stored
        dictionary = message.dictionary
        self.assertIsNotNone(dictionary)
        self.assertDictEqual(
            dictionary, {"jsonrpc": "2.0", "method": "test/test", "params": {}, "id": 10}
        )

    def test_create_notification(self):
        # If: I create a notification
        message = JSONRPCMessage.create_notification("test/test", {})

        # Then:
        # ... The message should have all the properties I defined
        self.assertIsNotNone(message)
        self.assertIsNone(message.message_id)
        self.assertEqual(message.message_method, "test/test")
        self.assertDictEqual(message.message_params, {})
        self.assertIsNone(message.message_result)
        self.assertIsNone(message.message_error)
        self.assertEqual(message.message_type, JSONRPCMessageType.Notification)

        # ... The dictionary should have the same values stored
        dictionary = message.dictionary
        self.assertIsNotNone(dictionary)
        self.assertDictEqual(
            dictionary, {"jsonrpc": "2.0", "method": "test/test", "params": {}}
        )

    # FROM DICTIONARY TESTS ################################################
    def test_from_dict_notification(self):
        # If: I create a notification message from a dictionary
        message = JSONRPCMessage.from_dictionary(
            {
                "method": "test/test",
                "params": {},
                # No ID = Notification
            }
        )

        # Then:
        # ... The message should have all the properties I defined
        self.assertIsNotNone(message)
        self.assertIsNone(message.message_id)
        self.assertEqual(message.message_method, "test/test")
        self.assertDictEqual(message.message_params, {})
        self.assertIsNone(message.message_result)
        self.assertIsNone(message.message_error)
        self.assertEqual(message.message_type, JSONRPCMessageType.Notification)

        # ... The dictionary should have the same values stored
        dictionary = message.dictionary
        self.assertIsNotNone(dictionary)
        self.assertDictEqual(
            dictionary, {"jsonrpc": "2.0", "method": "test/test", "params": {}}
        )

    def test_from_dict_invalid_notification(self):
        # If: I create a notification message from a dictionary that is missing a method
        # Then: I should get an exception
        with self.assertRaises(ValueError):
            JSONRPCMessage.from_dictionary(
                {
                    "params": {}
                    # No ID = Notification
                    # No method = Invalid
                }
            )

    def test_from_dict_response(self):
        # If: I create a successful response from a dictionary
        message = JSONRPCMessage.from_dictionary({"id": "10", "result": {}})

        # Then:
        # ... The message should have all the properties I defined
        self.assertIsNotNone(message)
        self.assertEqual(message.message_id, "10")
        self.assertIsNone(message.message_method)
        self.assertIsNone(message.message_params)
        self.assertIsNotNone(message.message_result)
        self.assertDictEqual(message.message_result, {})
        self.assertIsNone(message.message_error)
        self.assertEqual(message.message_type, JSONRPCMessageType.ResponseSuccess)

        # ... The dictionary should have the same values stored
        dictionary = message.dictionary
        self.assertIsNotNone(dictionary)
        self.assertDictEqual(dictionary, {"jsonrpc": "2.0", "result": {}, "id": "10"})

    def test_from_dict_error(self):
        # If: I create an error response from a dictionary
        message = JSONRPCMessage.from_dictionary(
            {"id": "10", "error": {"code": 20, "message": "msg", "data": {}}}
        )

        # Then:
        # ... The message should have all the properties I defined
        self.assertIsNotNone(message)
        self.assertEqual(message.message_id, "10")
        self.assertIsNone(message.message_method)
        self.assertIsNone(message.message_params)
        self.assertIsNone(message.message_result)
        self.assertIsNotNone(message.message_error)
        self.assertEqual(message.message_error["code"], 20)
        self.assertEqual(message.message_error["message"], "msg")
        self.assertDictEqual(message.message_error["data"], {})
        self.assertEqual(message.message_type, JSONRPCMessageType.ResponseError)

        # ... The dictionary should have the same values stored
        dictionary = message.dictionary
        self.assertIsNotNone(dictionary)
        self.assertDictEqual(
            dictionary,
            {
                "jsonrpc": "2.0",
                "error": {"code": 20, "message": "msg", "data": {}},
                "id": "10",
            },
        )

    def test_from_dict_response_invalid(self):
        # If: I create an invalid response from a dictionary
        # Then: I should get an exception
        with self.assertRaises(ValueError):
            JSONRPCMessage.from_dictionary({"id": "10", "error": {}, "result": {}})

    def test_from_dict_request(self):
        # If: I create a request from a dictionary
        message = JSONRPCMessage.from_dictionary(
            {"id": "10", "method": "test/test", "params": {}}
        )

        # Then:
        # ... The message should have all the properties I defined
        self.assertIsNotNone(message)
        self.assertEqual(message.message_id, "10")
        self.assertEqual(message.message_method, "test/test")
        self.assertDictEqual(message.message_params, {})
        self.assertIsNone(message.message_result)
        self.assertIsNone(message.message_error)
        self.assertEqual(message.message_type, JSONRPCMessageType.Request)

        # ... The dictionary should have the same values stored
        dictionary = message.dictionary
        self.assertIsNotNone(dictionary)
        self.assertDictEqual(
            dictionary, {"jsonrpc": "2.0", "method": "test/test", "params": {}, "id": "10"}
        )

    def test_from_dict_request_invalid(self):
        # If: I create an invalid request from a dictionary
        # Then: I should get an exception
        with self.assertRaises(ValueError):
            JSONRPCMessage.from_dictionary({"id": "10", "params": {}})


if __name__ == "__main__":
    unittest.main()
