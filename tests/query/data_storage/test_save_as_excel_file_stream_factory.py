# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from ossdbtoolsservice.query.contracts import SaveResultsRequestParams
from ossdbtoolsservice.query.data_storage import (
    SaveAsExcelFileStreamFactory,
    SaveAsExcelWriter,
    ServiceBufferFileStreamReader,
)


class TestSaveAsExcelFileStreamFactory(unittest.TestCase):
    def setUp(self):
        self.request = SaveResultsRequestParams()
        self.request.file_path = "TestPath"

        self.factory = SaveAsExcelFileStreamFactory(self.request)

    def test_get_reader(self):
        file_open_mock = mock.MagicMock()
        with mock.patch("io.open", new=file_open_mock):
            reader = self.factory.get_reader(self.request.file_path)

            self.assertIsInstance(reader, ServiceBufferFileStreamReader)

            file_open_mock.assert_called_once_with(self.request.file_path, "rb")

    def test_get_writer(self):
        file_open_mock = mock.MagicMock()
        xls_writter_mock = mock.MagicMock()

        with (
            mock.patch("io.open", new=file_open_mock),
            mock.patch("xlsxwriter.Workbook", new=xls_writter_mock),
        ):
            writer = self.factory.get_writer(self.request.file_path)

            self.assertIsInstance(writer, SaveAsExcelWriter)

            file_open_mock.assert_called_once_with(self.request.file_path, "w")
