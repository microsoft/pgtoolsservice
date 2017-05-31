# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import unittest

from pgsqltoolsservice.hosting import JsonRpcReader


class JsonRpcReaderTests(unittest.TestCase):
    def test_create_standard_encoding(self):
        with io.BytesIO(b'') as stream:
            # If: I create a JSON RPC reader with a stream without specifying the encoding
            reader = JsonRpcReader(stream)

            # Then: The stream and encoding should be set appropriately
            self.assertIsNotNone(reader)
            self.assertIs(reader.stream, stream)
            self.assertEqual(reader.encoding, 'UTF-8')
            self.assertEqual(reader._read_state, JsonRpcReader.ReadState.Header)
            
    def test_create_nonstandard_encoding(self):
        with io.BytesIO(b'') as stream:
            # If: I create a JSON RPC reader with a non-standard encoding
            reader = JsonRpcReader(stream, encoding="ascii")
            
            # Then: The stream and encoding should be set appropriately
            self.assertIsNotNone(reader)
            self.assertIs(reader.stream, stream)
            self.assertEqual(reader.encoding, 'ascii')
            self.assertEqual(reader._read_state, JsonRpcReader.ReadState.Header)
    
    def test_closes(self):
        with io.BytesIO(b'') as stream:
            # If:
            # ... I create a JSON RPC reader with an opened stream
            reader = JsonRpcReader(stream)

            # ... and I close the writer
            reader.close()

            # Then: The stream should be closed
            self.assertTrue(reader.stream.closed)

    # Read Next Chunk Tests

    def test_read_next_chunk_success(self):
        # Setup: Create a byte array for test input
        test_bytes = bytearray(b'123')

        with io.BytesIO(test_bytes) as stream:
            # If: I attempt to read a chunk from the stream
            reader = JsonRpcReader(stream)
            result = reader._read_next_chunk()

            # Then:
            # ... The result should be true
            self.assertTrue(result)

            # ... The buffer should contain 3 byte and should not have been read yet
            self.assertEqual(reader._buffer_end_offset, len(test_bytes))
            self.assertEqual(reader._read_offset, 0)

            # ... The buffer should now contain the bytes from the stream
            buffer_contents = reader._buffer[:len(test_bytes)]
            self.assertEqual(buffer_contents, test_bytes)

    def test_read_next_chunk_resize(self):
        # Setup: Create a byte array for test input
        test_bytes = bytearray(b'1234567890')

        with io.BytesIO(test_bytes) as stream:
            # If:
            # ... I create a reader with an artificially low initial buffer size
            #     and prefill the buffer
            reader = JsonRpcReader(stream)
            reader._buffer = bytearray(5)
            reader._buffer_end_offset = 4

            # ... and I read a chunk from the stream
            result = reader._read_next_chunk()

            # Then:
            # ... The read should have succeeded
            self.assertTrue(result, True)

            # ... The size of the buffer should have doubled
            self.assertEqual(len(reader._buffer), 10)

            # ... The buffer end offset should be the size of the buffer
            self.assertEqual(reader._buffer_end_offset, 10)

            # ... The buffer should contain the first 6 elements of the test data
            expected = test_bytes[:6]
            actual = reader._buffer[4:]
            self.assertEqual(actual, expected)

    def test_read_next_chunk_eof(self):
        with io.BytesIO() as stream:
            # If:
            # ... I create a reader with a stream that has no bytes
            reader = JsonRpcReader(stream)

            # ... and I read a chunk from the stream
            # Then: I should get an exception
            with self.assertRaises(EOFError):
                reader._read_next_chunk()

    def test_read_next_chunk_closed(self):
        # Setup: Create a stream that has already been closed
        stream = io.BytesIO()
        stream.close()

        # If:
        # ... I create a reader with a closed stream
        reader = JsonRpcReader(stream)

        # ... and I read a chunk from the stream
        # Then: I should get an exception
        with self.assertRaises(ValueError):
            reader._read_next_chunk()

    # Read Headers Tests

    def test_read_headers_success(self):
        # Setup: Create a reader with a loaded buffer that contains a a complete header
        reader = JsonRpcReader(None)
        reader._buffer = bytearray(b'Content-Length: 56\r\n\r\n')
        reader._buffer_end_offset = len(reader._buffer)

        # If: I look for a header block in the buffer
        result = reader._try_read_headers()

        # Then:
        # ... I should have found a header
        self.assertTrue(result)

        # ... The current reading position should have moved to the end of the buffer
        self.assertEqual(reader._read_offset, len(reader._buffer))
        self.assertEqual(reader._read_state, JsonRpcReader.ReadState.Content)

        # ... The headers should have been stored
        self.assertEqual(reader._expected_content_length, 56)
        self.assertDictEqual(reader._headers, {'content-length': '56'})

    def test_read_headers_not_found(self):
        # Setup: Create a reader with a loaded buffer that does not contain the \r\n\r\n control
        reader = JsonRpcReader(None)
        reader._buffer = bytearray(b'1234567890')
        reader._buffer_end_offset = len(reader._buffer)

        # If: I look for a header block in the buffer
        result = reader._try_read_headers()

        # Then:
        # ... I should not have found any
        self.assertFalse(result)

        # ... The current reading position of the buffer should not have moved
        self.assertEqual(reader._read_offset, 0)
        self.assertEqual(reader._read_state, JsonRpcReader.ReadState.Header)

    def test_read_headers_no_colon(self):
        # Setup: Create a reader with a buffer that contains the control sequence but does not
        #        match the header format
        test_buffer = bytearray(b'1234567890\r\n\r\n')
        reader = JsonRpcReader(None)
        reader._buffer = test_buffer
        reader._buffer_end_offset = len(reader._buffer)
        reader._read_offset = 1

        # If: I look for a header block in the buffer
        # Then:
        # ... I should get an exception b/c of the malformed header
        with self.assertRaises(KeyError):
            reader._try_read_headers()

        # ... The current reading position of the buffer should be reset to 0
        self.assertEqual(reader._read_offset, 0)

        # ... The buffer should have been trashed
        self.assertIsNot(reader._buffer, test_buffer)

    def test_read_headers_no_content_length(self):
        # Setup: Create a reader with a header block that doesn't contain content-length
        test_buffer = bytearray(b'Content-Type: application/json\r\n\r\n')
        reader = JsonRpcReader(None)
        reader._buffer = test_buffer
        reader._buffer_end_offset = len(reader._buffer)
        reader._read_offset = 1

        # If: I look for a header block in the buffer
        # Then:
        # ... I should get an exception from there not being a content-length header
        with self.assertRaises(LookupError):
            reader._try_read_headers()

        # ... The current reading position of the buffer should be reset to 0
        self.assertEqual(reader._read_offset, 0)

        # ... The buffer should have been trashed
        self.assertIsNot(reader._buffer, test_buffer)

        # ... The headers should have been trashed
        self.assertEqual(len(reader._headers), 0)

    def test_read_headers_bad_format(self):
        # Setup: Create a reader with a header block that contains invalid content-length
        test_buffer = bytearray(b'Content-Length: abc\r\n\r\n')
        reader = JsonRpcReader(None)
        reader._buffer = test_buffer
        reader._buffer_end_offset = len(reader._buffer)
        reader._read_offset = 1

        # If: I look for a header block in the buffer
        # Then:
        # ... I should get an exception from there not being a content-length header
        with self.assertRaises(LookupError):
            reader._try_read_headers()

        # ... The current reading position of the buffer should be reset to 0
        self.assertEqual(reader._read_offset, 0)

        # ... The buffer should have been trashed
        self.assertIsNot(reader._buffer, test_buffer)

        # ... The headers should have been trashed
        self.assertEqual(len(reader._headers), 0)

    # Try Read Content Tests

    def test_read_content_success(self):
        # Setup: Create a reader that has read in headers and has all of a message buffered
        test_buffer = bytearray(b"message")
        reader = JsonRpcReader(None)
        reader._buffer = test_buffer
        reader._buffer_end_offset = len(reader._buffer)
        reader._read_offset = 0
        reader._read_state = JsonRpcReader.ReadState.Content
        reader._expected_content_length = 5

        # If: I read a message from the buffer
        output = ['']
        result = reader._try_read_content(output)

        # Then:
        # ... The message should be successfully read
        self.assertTrue(result)
        self.assertEqual(output[0], 'messa')

        # ... The state of the reader should have been updated
        self.assertEqual(reader._read_state, JsonRpcReader.ReadState.Header)
        self.assertEqual(reader._read_offset, 5)
        self.assertEqual(reader._buffer_end_offset, len(reader._buffer))

    def test_read_content_not_enough_buffer(self):
        # Setup: Create a reader that has read in headers and has part of a message buffered
        test_buffer = bytearray(b'message')
        reader = JsonRpcReader(None)
        reader._buffer = test_buffer
        reader._buffer_end_offset = len(reader._buffer)
        reader._read_offset = 0
        reader._read_state = JsonRpcReader.ReadState.Content
        reader._expected_content_length = 15

        # If: I read a message from the buffer
        output = ['']
        result = reader._try_read_content(output)

        # Then:
        # ... The result should be false and the output should be empty
        self.assertFalse(result)
        self.assertEqual(output[0], '')

        # ... The state of the reader should stay the same
        self.assertEqual(reader._read_state, JsonRpcReader.ReadState.Content)
        self.assertEqual(reader._read_offset, 0)
        self.assertEqual(reader._expected_content_length, 15)
        self.assertEqual(reader._buffer_end_offset, len(reader._buffer))

    # Read Message Tests

    def test_read_message_single_read(self):
        # Setup: Reader with a stream that has an entire message read
        test_bytes = bytearray(b'Content-Length: 32\r\n\r\n{"method":"test", "params":null}')
        with io.BytesIO(test_bytes) as stream:
            reader = JsonRpcReader(stream)
            reader._buffer = bytearray(100)

            # If: I read a message with the reader
            message = reader.read_message()

            # Then:
            # ... I should have a successful message
            self.assertIsNotNone(message)

            # ... The reader should be back in header mode
            self.assertEqual(reader._read_state, JsonRpcReader.ReadState.Header)

            # ... The buffer should have been trimmed
            self.assertEqual(len(reader._buffer), JsonRpcReader.DEFAULT_BUFFER_SIZE)

    def test_read_message_multi_read_header(self):
        # Setup: Reader with a stream that has an entire message read
        test_bytes = bytearray(b'Content-Length: 32\r\n\r\n{"method":"test", "params":null}')
        with io.BytesIO(test_bytes) as stream:
            reader = JsonRpcReader(stream)
            reader._buffer = bytearray(10)

            # If: I read a message with the reader
            message = reader.read_message()

            # Then:
            # ... I should have a successful message
            self.assertIsNotNone(message)

            # ... The reader should be back in header mode
            self.assertEqual(reader._read_state, JsonRpcReader.ReadState.Header)

            # ... The buffer should have been trimmed
            self.assertEqual(len(reader._buffer), JsonRpcReader.DEFAULT_BUFFER_SIZE)

    def test_read_message_multi_read_content(self):
        # Setup: Reader with a stream that has an entire message read
        test_bytes = bytearray(b'Content-Length: 32\r\n\r\n{"method":"test", "params":null}')
        with io.BytesIO(test_bytes) as stream:
            reader = JsonRpcReader(stream)
            reader._buffer = bytearray(25)

            # If: I read a message with the reader
            message = reader.read_message()

            # Then:
            # ... I should have a successful message
            self.assertIsNotNone(message)

            # ... The reader should be back in header mode
            self.assertEqual(reader._read_state, JsonRpcReader.ReadState.Header)

            # ... The buffer should have been trimmed
            self.assertEqual(len(reader._buffer), JsonRpcReader.DEFAULT_BUFFER_SIZE)

    def test_read_message_invalid_json(self):
        # Setup: Reader with a stream that has an invalid message
        test_bytes = bytearray(b'Content-Length: 10\r\n\r\nabcdefghij')
        with io.BytesIO(test_bytes) as stream:
            reader = JsonRpcReader(stream)
            reader._buffer = bytearray(100)

            # If: I read a message
            # Then:
            # ... It should throw an exception
            with self.assertRaises(ValueError):
                reader.read_message()

            # ... The buffer should be trashed
            self.assertEqual(len(reader._buffer), reader.DEFAULT_BUFFER_SIZE)

    def test_read_multiple_messages(self):
        test_string = b'Content-Length: 32\r\n\r\n{"method":"test", "params":null}'
        test_bytes = bytearray(test_string + test_string)
        with io.BytesIO(test_bytes) as stream:
            reader = JsonRpcReader(stream)
            reader._buffer = bytearray(100)

            # If:
            # ... I read a message
            msg1 = reader.read_message()

            # ... And I read another message
            msg2 = reader.read_message()

            # Then:
            # ... The messages should be real
            self.assertIsNotNone(msg1)
            self.assertIsNotNone(msg2)

            # ... The buffer should have been trashed
            self.assertEqual(len(reader._buffer), reader.DEFAULT_BUFFER_SIZE)

    def test_read_recover_from_header_message(self):
        test_string = b'Content-Type: application/json\r\n\r\n' +\
                      b'Content-Length: 32\r\n\r\n{"method":"test", "params":null}'
        test_bytes = bytearray(test_string)
        with io.BytesIO(test_bytes) as stream:
            reader = JsonRpcReader(stream)
            reader._buffer = bytearray(100)

            # If: I read a message with invalid headers
            # Then: I should get an exception
            with self.assertRaises(LookupError):
                reader.read_message()

            # If: I read another valid message
            msg = reader.read_message()

            # Then: I should have a valid message
            self.assertIsNotNone(msg)

    def test_read_recover_from_content_message(self):
        test_string = b'Content-Length: 10\r\n\r\nabcdefghij' + \
                      b'Content-Length: 32\r\n\r\n{"method":"test", "params":null}'
        test_bytes = bytearray(test_string)
        with io.BytesIO(test_bytes) as stream:
            reader = JsonRpcReader(stream)
            reader._buffer = bytearray(100)

            # If: I read a message with invalid content
            # Then: I should get an exception
            with self.assertRaises(ValueError):
                reader.read_message()

            # If: I read another valid message
            msg = reader.read_message()

            # Then: I should have a valid message
            self.assertIsNotNone(msg)

