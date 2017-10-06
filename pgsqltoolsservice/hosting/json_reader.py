# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
import json

from pgsqltoolsservice.hosting.json_message import JSONRPCMessage


class JSONRPCReader:
    """
    Reads JSON RPC message from a stream
    """

    # CONSTANTS ############################################################
    CR = 13
    LF = 10
    BUFFER_RESIZE_TRIGGER = 0.25
    DEFAULT_BUFFER_SIZE = 8192

    class ReadState(Enum):
        Header = 1,
        Content = 2

    # CONSTRUCTOR ##########################################################
    def __init__(self, stream, encoding=None, logger=None):
        """
        Initializes the JSON RPC reader
        :param stream: Stream that messages will be read from
        :param encoding: Optional encoding choice for messages. Defaults to UTF-8
        :param logger: Optional destination for logging
        """
        self.stream = stream
        self.encoding = encoding or 'UTF-8'
        self._logger = logger

        self._buffer = bytearray(self.DEFAULT_BUFFER_SIZE)
        # Pointer to end of buffer content
        self._buffer_end_offset = 0
        # Pointer to where we have read up to
        self._read_offset = 0

        # Setup message reading state
        self._expected_content_length = 0
        self._headers = {}
        self._read_state = self.ReadState.Header
        self._needs_more_data = True

    # METHODS ##############################################################
    def close(self):
        """
        Close the stream
        """
        try:
            self.stream.close()
        except Exception as e:
            if self._logger is not None:
                self._logger.exception(f'Exception raised when reader stream closed: {e}')

    def read_message(self):
        """
        Read JSON RPC message from buffer
        :raises ValueError: if the body-content cannot be serialized to a JSON object
        :return: JsonRpcMessage that was received
        """
        # Using a mutable list to hold the value since an immutable string passed by reference won't
        # change the value
        content = ['']
        try:
            while not self._needs_more_data or self._read_next_chunk():
                # We should have all the data we need to form a message in the buffer. If we need
                # more data to form the next message, this flag will be reset by an attempt to form
                # a header or content
                self._needs_more_data = False

                # If we can't read a header, read the next chunk
                if self._read_state is self.ReadState.Header and not self._try_read_headers():
                    self._needs_more_data = True
                    continue

                # If we read the header, try the content. If that fails, read the next chunk
                if self._read_state is self.ReadState.Content and not self._try_read_content(content):
                    self._needs_more_data = True
                    continue

                # We have the content
                break

            # Uncomment for verbose logging
            if self._logger is not None:
                self._logger.debug(f'{content[0]}')

            return JSONRPCMessage.from_dictionary(json.loads(content[0]))
        except ValueError as ve:
            # Response has invalid json object
            if self._logger is not None:
                self._logger.warn('JSON RPC reader on read_message() encountered exception: {}'.format(ve))
            raise
        finally:
            # Remove the bytes that have been read
            self._trim_buffer_and_resize(self._read_offset)

    # IMPLEMENTATION DETAILS ###############################################

    def _read_next_chunk(self):
        """
        Read a chunk from the output stream into buffer
        :raises EOFError: Stream was empty or stream did not contain a valid header or content-body
        :raises ValueError: Stream was closed externally
        :return: True on successful read of a message chunk
        """
        # Check if we need to resize the buffer
        current_buffer_size = len(self._buffer)
        if (current_buffer_size - self._buffer_end_offset) / current_buffer_size < self.BUFFER_RESIZE_TRIGGER:
            # Resize the buffer, copy the old contents, and point to the new buffer
            resized_buffer = bytearray(current_buffer_size * 2)
            resized_buffer[0:current_buffer_size] = self._buffer
            self._buffer = resized_buffer

        # Memory view is required in order to read into a subset of a byte array
        try:
            length_read = self.stream.readinto(memoryview(self._buffer)[self._buffer_end_offset:])

            if not length_read:
                if self._logger is not None:
                    self._logger.warn('JSON RPC Reader reached end of stream')
                raise EOFError('End of stream reached, no output.')

            self._buffer_end_offset += length_read

            return True
        except ValueError as ex:
            # Stream was closed
            if self._logger is not None:
                self._logger.warn('JSON RPC Reader on read_next_chunk encountered exception: {}'.format(ex))
            raise

    def _try_read_headers(self):
        """
        Try to read the header information from the internal buffer expecting the last header to contain '\r\n\r\n'
        :raises LookupError: The content-length header was not found
        :raises ValueError: The content-length contained an invalid literal for int
        :raises KeyError: The header block was malformed by not having a key:value format
        :return: True on successful read of headers, False on failure to find headers
        """
        # Scan the buffer up until right before the \r\n\r\n
        scan_offset = self._read_offset
        while scan_offset + 3 < self._buffer_end_offset and (
            self._buffer[scan_offset] != self.CR or
            self._buffer[scan_offset + 1] != self.LF or
            self._buffer[scan_offset + 2] != self.CR or
            self._buffer[scan_offset + 3] != self.LF
        ):
            scan_offset += 1

        # If we reached the end of the buffer and haven't found the control sequence, we haven't found the headers
        if scan_offset + 3 >= self._buffer_end_offset:
            return False

        # Split the headers by newline
        try:
            headers_read = self._buffer[self._read_offset:scan_offset].decode('ascii')
            for header in headers_read.split('\n'):
                colon_index = header.find(':')

                # Make sure there's a colon to split key and value on
                if colon_index == -1:
                    if self._logger is not None:
                        self._logger.warn('JSON RPC reader encountered missing colons in try_read_headers()')
                    raise KeyError('Colon missing from header: {}'.format(header))

                # Case insensitive check
                header_key = header[:colon_index].strip().lower()
                header_value = header[colon_index + 1:].strip()
                self._headers[header_key] = header_value

            # Was content-length found?
            if 'content-length' not in self._headers:
                if self._logger is not None:
                    self._logger.warn('JSON RPC reader did not find Content-Length in the headers')
                raise LookupError('Content-Length was not found in headers received.')

            self._expected_content_length = int(self._headers['content-length'])

        except (ValueError, KeyError, LookupError):
            # ValueError: Content-Length contained invalid literal for int
            # KeyError: Headers were malformed due to missing colon
            # LookupError: Content-Length header was not found
            self._trim_buffer_and_resize(scan_offset + 4)
            raise

        # Pushing read pointer past the newline character
        self._read_offset = scan_offset + 4
        self._read_state = self.ReadState.Content

        return True

    def _try_read_content(self, content):
        """
        Try to read content from internal buffer
        :param content: Location to store the content
        :return: True on successful reading of content, False on incomplete read of content (based on content-length)
        """
        # TODO: Take into consideration that the implementation of this protocol should place
        #       2 CRLF after the completion of the message.
        if self._buffer_end_offset - self._read_offset < self._expected_content_length:
            # We buffered less than the expected content length
            return False

        content[0] = self._buffer[self._read_offset:self._read_offset + self._expected_content_length]\
            .decode(self.encoding)
        self._read_offset += self._expected_content_length

        self._read_state = self.ReadState.Header

        return True

    def _trim_buffer_and_resize(self, bytes_to_remove):
        """
        Trim the buffer by the passed in bytes_to_remove by creating a new buffer that is at a minimum the
        default max size
        :param bytes_to_remove: Number of bytes to remove from the current buffer
        """
        current_buffer_size = len(self._buffer)

        # Create a new buffer with either minimum size of leftover size
        new_buffer = bytearray(max(current_buffer_size - bytes_to_remove, self.DEFAULT_BUFFER_SIZE))

        # If we have content we did not read, copy that portion to the new buffer
        if bytes_to_remove <= current_buffer_size:
            new_buffer[:self._buffer_end_offset - bytes_to_remove] = \
                self._buffer[bytes_to_remove:self._buffer_end_offset]

        # Point to the new buffer
        self._buffer = new_buffer

        # Reset pointers after the shift
        self._read_offset = 0
        self._buffer_end_offset -= bytes_to_remove

        # Reset the headers
        self._headers = {}
