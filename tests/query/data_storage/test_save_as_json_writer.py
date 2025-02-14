# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from ossdbtoolsservice.query.contracts import DbCellValue, DbColumn
from ossdbtoolsservice.query.data_storage import SaveAsJsonWriter
from ossdbtoolsservice.query_execution.contracts import SaveResultsAsJsonRequestParams


class TestSaveAsJsonWriter(unittest.TestCase):
    def setUp(self):
        self.request = SaveResultsAsJsonRequestParams()
        self.request.file_path = "TestPath"
        self.request.include_headers = True

        self.mock_io = mock.MagicMock()

        self.row = [
            DbCellValue("Test", False, None, 0),
            DbCellValue(1023, False, None, 0),
            DbCellValue(False, False, None, 0),
        ]

        name_column = DbColumn()
        name_column.column_name = "Name"

        id_column = DbColumn()
        id_column.column_name = "Id"

        is_valid_column = DbColumn()
        is_valid_column.column_name = "Valid"

        self.columns = [name_column, id_column, is_valid_column]

        self.worksheet_mock = mock.MagicMock()
        self.workbook_mock = mock.MagicMock()
        self.workbook_mock.add_worksheet = mock.Mock(return_value=self.worksheet_mock)
        self.xlsxwriter_mock = mock.Mock(return_value=self.workbook_mock)
        self.mock_io.name = "SomeName"

        with mock.patch("xlsxwriter.Workbook", new=self.xlsxwriter_mock):
            self.writer = SaveAsJsonWriter(self.mock_io, self.request)

    def test_write_row(self):
        self.writer.write_row(self.row, self.columns)

        self.assertEqual(1, len(self.writer._data))

        self.assertEqual("Test", self.writer._data[0]["Name"])
        self.assertEqual("1023", self.writer._data[0]["Id"])
        self.assertEqual("False", self.writer._data[0]["Valid"])

    def test_complete_write(self):
        json_dump_mock = mock.MagicMock()

        with mock.patch("json.dump", new=json_dump_mock):
            self.writer.complete_write()
            json_dump_mock.assert_called_once_with(
                self.writer._data, self.mock_io, indent=True
            )
