import unittest

from pgsqltoolsservice.hosting import JsonRpcMessage, JsonRpcMessageType


class JsonRpcMessageTests(unittest.TestCase):
    def test_create_error(self):
        # If: I create an error message
        message = JsonRpcMessage.create_error(10, 20, 'msg', {})

        # Then:
        # ... The message should have all the properties I defined
        self.assertIsNotNone(message)
        self.assertEqual(message.message_id, 10)
        self.assertIsNone(message.message_method)
        self.assertIsNone(message.message_params)
        self.assertIsNone(message.message_result)
        self.assertIsNotNone(message.message_error)
        self.assertEqual(message.message_error['code'], 20)
        self.assertEqual(message.message_error['message'], 'msg')
        self.assertDictEqual(message.message_error['data'], {})
        self.assertEqual(message.message_type, JsonRpcMessageType.ResponseError)

        # ... The dictionary should have the same values stored
        dictionary = message.dictionary
        self.assertIsNotNone(dictionary)
        self.assertDictEqual(dictionary, {
            u'jsonrpc': u'2.0',
            u'error': {
                u'code': 20,
                u'message': 'msg',
                u'data': {}
            },
            u'id': 10
        })

    def test_create_response(self):
        # If I create a response
        message = JsonRpcMessage.create_response(10, {})

        # Then:
        # ... The message should have all the properties I defined
        self.assertIsNotNone(message)
        self.assertEqual(message.message_id, 10)
        self.assertIsNone(message.message_method)
        self.assertIsNone(message.message_params)
        self.assertIsNotNone(message.message_result)
        self.assertDictEqual(message.message_result, {})
        self.assertIsNone(message.message_error)
        self.assertEqual(message.message_type, JsonRpcMessageType.ResponseSuccess)

        # ... The dictionary should have the same values stored
        dictionary = message.dictionary
        self.assertIsNotNone(dictionary)
        self.assertDictEqual(dictionary, {
            u'jsonrpc': u'2.0',
            u'result': {},
            u'id': 10
        })

if __name__ == '__main__':
    unittest.main()
