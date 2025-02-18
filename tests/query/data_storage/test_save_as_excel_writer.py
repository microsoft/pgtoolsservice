# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from ossdbtoolsservice.query.contracts import DbCellValue, DbColumn
from ossdbtoolsservice.query.data_storage import SaveAsExcelWriter
from ossdbtoolsservice.query_execution.contracts import SaveResultsAsExcelRequestParams


class TestSaveAsExcelWriter(unittest.TestCase):
    def setUp(self):
        self.request = SaveResultsAsExcelRequestParams()
        self.request.file_path = "TestPath"
        self.request.include_headers = True

        self.mock_io = mock.MagicMock()

        self.row = [
            DbCellValue("Test", False, "Test", 0),
            DbCellValue(1023, False, 1023, 0),
            DbCellValue(False, False, False, 0),
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
            self.writer = SaveAsExcelWriter(self.mock_io, self.request)

    def test_construction(self):
        self.xlsxwriter_mock.assert_called_once_with(self.mock_io.name)
        self.workbook_mock.add_worksheet.assert_called_once()

    def test_write_row_column_headers(self):
        bold = {}
        self.workbook_mock.add_format = mock.Mock(return_value=bold)
        self.writer.write_row(self.row, self.columns)
        self.workbook_mock.add_format.assert_called_once_with({"bold": 1})

        write_column_header_args = self.worksheet_mock.write.call_args_list

        # See https://github.com/microsoft/pgtoolsservice/pull/491
        self.assertEqual(0, write_column_header_args[0][0][1])
        self.assertEqual("Name", write_column_header_args[0][0][2])
        self.assertEqual(bold, write_column_header_args[0][0][3])

        self.assertEqual(1, write_column_header_args[1][0][1])
        self.assertEqual("Id", write_column_header_args[1][0][2])
        self.assertEqual(bold, write_column_header_args[1][0][3])

        self.assertEqual(2, write_column_header_args[2][0][1])
        self.assertEqual("Valid", write_column_header_args[2][0][2])
        self.assertEqual(bold, write_column_header_args[2][0][3])

    def test_write_row(self):
        self.writer.write_row(self.row, self.columns)

        write_column_value_args = self.worksheet_mock.write.call_args_list

        self.assertEqual(1, write_column_value_args[3][0][0])
        self.assertEqual(0, write_column_value_args[3][0][1])
        self.assertEqual("Test", write_column_value_args[3][0][2])

        self.assertEqual(1, write_column_value_args[4][0][0])
        self.assertEqual(1, write_column_value_args[4][0][1])
        self.assertEqual(1023, write_column_value_args[4][0][2])

        self.assertEqual(1, write_column_value_args[5][0][0])
        self.assertEqual(2, write_column_value_args[5][0][1])
        self.assertEqual(False, write_column_value_args[5][0][2])

    def test_complete_write(self):
        self.writer.complete_write()
        self.workbook_mock.close.assert_called_once()
