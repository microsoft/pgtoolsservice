# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import unittest
from unittest import mock

from pgsqltoolsservice.edit_data import DataEditorSession
from pgsqltoolsservice.edit_data.contracts import InitializeEditParams, EditInitializerFilter
from tests.utils import MockConnection
from pgsqltoolsservice.edit_data import EditTableMetadata, EditColumnMetadata, DataEditSessionExecutionState
from pgsqltoolsservice.query_execution.query import Query, Batch, ExecutionState
from pgsqltoolsservice.query_execution.result_set import ResultSet


class TestDataEditorSession(unittest.TestCase):

    def setUp(self):
        self._metadata_factory = mock.MagicMock()
        self._connection = MockConnection({"port": "8080", "host": "test", "dbname": "test"})
        self._initialize_edit_request = InitializeEditParams()

        self._initialize_edit_request.schema_name = 'public'
        self._initialize_edit_request.object_name = 'Employee'
        self._initialize_edit_request.object_type = 'Table'

        column = EditColumnMetadata()
        column.escaped_name = 'TestColumn'

        self._columns_metadata = [column]
        self._edit_table_metadata = EditTableMetadata(self._columns_metadata)

        self._edit_table_metadata.escaped_multipart_name = 'TestTable'

        self._query_executer = mock.MagicMock()
        self._on_success = mock.MagicMock()
        self._on_failure = mock.MagicMock()
        self._data_editor_session = DataEditorSession(self._metadata_factory)

        self._metadata_factory.get = mock.Mock(return_value=self._edit_table_metadata)

        self._query = 'SELECT TESTCOLUMN FROM TESTTABLE LIMIT 100'

        self._data_editor_session._construct_initialize_query = mock.Mock(return_value=self._query)

    def test_initialize_gets_metadata(self):

        self._data_editor_session.initialize(self._initialize_edit_request, self._connection, self._query_executer, self._on_success, self._on_failure)

        self.assertEqual(self._edit_table_metadata, self._data_editor_session.table_metadata)
        self._metadata_factory.get.assert_called_once()

        call_args = self._metadata_factory.get.call_args[0]

        self.assertEqual(self._connection, call_args[0])
        self.assertEqual(self._initialize_edit_request.schema_name, call_args[1])
        self.assertEqual(self._initialize_edit_request.object_name, call_args[2])
        self.assertEqual(self._initialize_edit_request.object_type, call_args[3])

    def test_initialize_calls_queryexecuter_with_query_with_filters(self):

        self._initialize_edit_request.filters = EditInitializerFilter()

        self._initialize_edit_request.filters.limit_results = 100

        self._data_editor_session.initialize(self._initialize_edit_request, self._connection, self._query_executer, self._on_success, self._on_failure)

        self.assertEqual(self._query_executer.call_args[0][0].upper(), 'SELECT TESTCOLUMN FROM TESTTABLE LIMIT 100')

        self._query_executer.assert_called_once()

    def test_initialize_when_query_is_null(self):
        self._query_executer = mock.MagicMock(return_value=DataEditSessionExecutionState(None))

        self._data_editor_session.initialize(self._initialize_edit_request, self._connection, self._query_executer, self._on_success, self._on_failure)

        self._on_failure.assert_called_once()

    def test_initialize_calls_failure_when_query_status_is_not_executed(self):
        query = Query('owner', '')
        self._query_executer = mock.MagicMock(return_value=DataEditSessionExecutionState(query))

        self._data_editor_session.initialize(self._initialize_edit_request, self._connection, self._query_executer, self._on_success, self._on_failure)

        self._on_failure.assert_called_once()

    def test_initialize_calls_success(self):
        query = Query('owner', '')
        query.execution_state = ExecutionState.EXECUTED

        rows = [("Result1", 53), ("Result2", None,)]
        result_set = ResultSet(0, 0, None, len(rows), rows)

        batch = Batch('', 1, None)
        batch.result_set = result_set

        query.batches = [batch]
        self._query_executer = mock.MagicMock(return_value=DataEditSessionExecutionState(query))

        self._data_editor_session.initialize(self._initialize_edit_request, self._connection, self._query_executer, self._on_success, self._on_failure)

        self.assertTrue(self._data_editor_session._is_initialized)
        self.assertTrue(self._data_editor_session._next_row_id == len(rows))
        self.assertEqual(result_set, self._data_editor_session._result_set)

        self._on_success.assert_called_once()

    def test_update_cell_when_in_cache(self):
        row_id = 0
        column_index = 0
        new_value = 'Updates'

        edit_row = mock.MagicMock()

        edit_row.set_cell_value = mock.MagicMock(return_value=new_value)

        self._data_editor_session._session_cache[row_id] = edit_row

        result = self._data_editor_session.update_cell(row_id, column_index, new_value)

        self.assertEqual(new_value, result)


if __name__ == '__main__':
    unittest.main()
