# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from pgsqltoolsservice.query.contracts import DbColumn, DbCellValue
from pgsqltoolsservice.query.data_storage import SaveAsCsvWriter
from pgsqltoolsservice.query_execution.contracts import SaveResultsAsCsvRequestParams


class TestSaveAsCsvWriter(unittest.TestCase):

    def setUp(self):
        self.request = SaveResultsAsCsvRequestParams()
        self.request.file_path = 'TestPath'
        self.request.include_headers = True

        self.mock_io = mock.MagicMock()

        self.row = [
            DbCellValue('Test', False, None, 0),
            DbCellValue(1023, False, None, 0),
            DbCellValue(False, False, None, 0)
        ]

        name_column = DbColumn()
        name_column.column_name = 'Name'

        id_column = DbColumn()
        id_column.column_name = 'Id'

        is_valid_column = DbColumn()
        is_valid_column.column_name = 'Valid'

        self.columns = [
            name_column,
            id_column,
            is_valid_column
        ]

        self.writer = SaveAsCsvWriter(self.mock_io, self.request)

    def test_write_row(self):

        writer_mock = mock.MagicMock()
        csv_writer_mock = mock.Mock(return_value=writer_mock)
        with mock.patch('csv.writer', new=csv_writer_mock):
            self.writer.write_row(self.row, self.columns)

            csv_writer_mock.assert_called_once_with(self.mock_io, delimiter=',', quotechar='"', quoting=0)

            self.assertEqual(writer_mock.writerow.call_count, 2)
            write_row_args = writer_mock.writerow.call_args_list

            self.assertEqual(['Name', 'Id', 'Valid'], write_row_args[0][0][0])
            self.assertEqual(['Test', '1023', 'False'], write_row_args[1][0][0])

    def test_write_row_for_few_columns(self):

        self.writer._column_start_index = 1
        self.writer._column_end_index = 2

        writer_mock = mock.MagicMock()
        csv_writer_mock = mock.Mock(return_value=writer_mock)
        with mock.patch('csv.writer', new=csv_writer_mock):
            self.writer.write_row(self.row, self.columns)

            csv_writer_mock.assert_called_once_with(self.mock_io, delimiter=',', quotechar='"', quoting=0)

            self.assertEqual(writer_mock.writerow.call_count, 2)
            write_row_args = writer_mock.writerow.call_args_list

            self.assertEqual(['Id', 'Valid'], write_row_args[0][0][0])
            self.assertEqual(['1023', 'False'], write_row_args[1][0][0])
