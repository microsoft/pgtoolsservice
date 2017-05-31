# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import json
import os
import re
import unittest

from pgsqltoolsservice.hosting import JsonRpcWriter, JsonRpcMessage, JsonRpcMessageType


class JsonRpcWriterTests(unittest.TestCase):
    def test_create_standard_encoding(self):
        with io.BytesIO(b'123') as stream:
            # If: I create a JSON RPC writer
            writer = JsonRpcWriter(stream)

            # Then: The available properties should be set properly
            self.assertIsNotNone(writer)
            self.assertIs(writer.stream, stream)
            self.assertEqual(writer.encoding, 'UTF-8')
            self.assertEqual(writer._logger, None)

    def test_create_nonstandard_encoding(self):
        with io.BytesIO(b'123') as stream:
            # If: I create a JSON RPC writer with a nonstandard encoding
            writer = JsonRpcWriter(stream, 'ascii')

            # Then: The available properties should be set properly
            self.assertIsNotNone(writer)
            self.assertIs(writer.stream, stream)
            self.assertEqual(writer.encoding, 'ascii')
            self.assertEqual(writer._logger, None)

    def test_close(self):
        with io.BytesIO(b'123') as stream:
            # If:
            # ... I create a JSON RPC writer with an opened stream
            writer = JsonRpcWriter(stream)

            # ... and I close the writer
            writer.close()

            # Then: The stream should be closed
            self.assertTrue(writer.stream.closed)

    def test_send_message(self):
        with io.BytesIO(b'') as stream:
            # If:
            # ... I create a JSON RPC writer
            writer = JsonRpcWriter(stream)

            # ... and I send a message
            message = JsonRpcMessage.create_request('123', 'test/test', {})
            writer.send_message(message)

            # Then:
            # ... The content-length header should be present
            stream.seek(0)
            header = stream.readline().decode('ascii')
            self.assertRegex(header, re.compile('^Content-Length: [0-9]+\r\n$', re.IGNORECASE))

            # ... There should be a blank line to signify the end of the headers
            blank_line = stream.readline().decode('ascii')
            self.assertEqual(blank_line, '\r\n')

            # ... The JSON message as a dictionary should match the dictionary of the message
            message_str = str.join(os.linesep, [x.decode('UTF-8') for x in stream.readlines()])
            message_dict = json.loads(message_str)
            self.assertDictEqual(message_dict, message.dictionary)

    # TODO: test_send_message_logged
