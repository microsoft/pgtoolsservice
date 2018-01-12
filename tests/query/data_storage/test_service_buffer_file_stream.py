# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

import pgsqltoolsservice.query.data_storage.service_buffer_file_stream as stream
from pgsqltoolsservice.query.data_storage import ServiceBufferFileStreamWriter, ServiceBufferFileStreamReader


class TestServiceBufferFileStream(unittest.TestCase):

    def setUp(self):
        self._file_name = 'testFile'

    def test_get_file_name(self):
        tempfile_mock = mock.MagicMock()
        tempfile_mock.mkstemp = mock.Mock(return_value=(1, self._file_name))
        with mock.patch('pgsqltoolsservice.query.data_storage.service_buffer_file_stream.tempfile', new=tempfile_mock):
            stream.create_file()
            tempfile_mock.mkstemp.assert_called_once()

    def test_get_reader(self):
        io_mock = mock.MagicMock()

        with mock.patch('pgsqltoolsservice.query.data_storage.service_buffer_file_stream.io', new=io_mock):
            reader = stream.get_reader(self._file_name)

            self.assertIsInstance(reader, ServiceBufferFileStreamReader)
            io_mock.open.assert_called_once_with(self._file_name, 'rb')

    def test_get_writer(self):
        io_mock = mock.MagicMock()

        with mock.patch('pgsqltoolsservice.query.data_storage.service_buffer_file_stream.io', new=io_mock):
            writer = stream.get_writer(self._file_name)

            self.assertIsInstance(writer, ServiceBufferFileStreamWriter)
            io_mock.open.assert_called_once_with(self._file_name, 'wb')


if __name__ == '__main__':
    unittest.main()
