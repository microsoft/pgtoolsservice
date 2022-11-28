# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List  # noqa
import unittest
from unittest import mock

from ossdbtoolsservice.edit_data import (DataEditorSession,
                                         DataEditSessionExecutionState,
                                         EditColumnMetadata, EditTableMetadata)
from ossdbtoolsservice.edit_data.contracts import CreateRowResponse  # noqa
from ossdbtoolsservice.edit_data.contracts import (EditInitializerFilter,
                                                   InitializeEditParams)
from ossdbtoolsservice.edit_data.update_management import RowDelete
from ossdbtoolsservice.edit_data.update_management.row_edit import EditScript
from ossdbtoolsservice.query import (
    Batch, ExecutionState, Query, QueryEvents, QueryExecutionSettings,
    ResultSet, ResultSetStorageType, create_result_set)
from ossdbtoolsservice.query.contracts import DbColumn
from ossdbtoolsservice.utils.constants import MYSQL_PROVIDER_NAME
from tests.mysqlsmo_tests.utils import MockMySQLServerConnection
from tests.utils import MockPyMySQLCursor


class TestMySQLDataEditorSession(unittest.TestCase):

    def setUp(self):
        self._metadata_factory = mock.MagicMock()
        self._mock_cursor = MockPyMySQLCursor(None)
        self._connection = MockMySQLServerConnection(cur=self._mock_cursor)
        self._initialize_edit_request = InitializeEditParams()

        self._initialize_edit_request.schema_name = 'public'
        self._initialize_edit_request.object_name = 'Employee'
        self._initialize_edit_request.object_type = 'Table'

        db_column = DbColumn()

        column = EditColumnMetadata(db_column, None)

        self._columns_metadata = [column]
        self._schema_name = 'public'
        self._table_name = 'table'
        self._edit_table_metadata = EditTableMetadata(self._schema_name, self._table_name, self._columns_metadata, MYSQL_PROVIDER_NAME)

        self._query_executer = mock.MagicMock()
        self._on_success = mock.MagicMock()
        self._on_failure = mock.MagicMock()
        self._data_editor_session = DataEditorSession(self._metadata_factory)

        self._metadata_factory.get = mock.Mock(return_value=self._edit_table_metadata)

        self._query = 'SELECT TESTCOLUMN FROM TESTTABLE LIMIT 100'

        self._data_editor_session._construct_initialize_query = mock.Mock(return_value=self._query)

    def get_result_set(self, rows: List[tuple]) -> ResultSet:
        result_set = create_result_set(ResultSetStorageType.IN_MEMORY, 0, 0)
        cursor = MockPyMySQLCursor(rows)

        columns_info = []
        get_column_info_mock = mock.Mock(return_value=columns_info)

        with mock.patch('ossdbtoolsservice.query.in_memory_result_set.get_columns_info', new=get_column_info_mock):
            result_set.read_result_to_end(cursor)

        return result_set

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

        self._query_executer.assert_called_once()

    def test_initialize_calls_failure_when_query_status_is_not_executed(self):
        query = Query('owner', '', QueryExecutionSettings(None, None), QueryEvents())
        self._query_executer = mock.MagicMock(return_value=DataEditSessionExecutionState(query))

        self._data_editor_session.initialize(self._initialize_edit_request, self._connection, self._query_executer, self._on_success, self._on_failure)

        self._query_executer.assert_called_once()

    def test_initialize_calls_success(self):
        query = Query('owner', '', QueryExecutionSettings(None, None), QueryEvents())
        query._execution_state = ExecutionState.EXECUTED

        rows = [("Result1", 53), ("Result2", None,)]
        result_set = self.get_result_set(rows)

        batch = Batch('', 1, None)
        batch._result_set = result_set

        query._batches = [batch]
        self._query_executer = mock.MagicMock(return_value=DataEditSessionExecutionState(query))

        self._data_editor_session.initialize(self._initialize_edit_request, self._connection, self._query_executer, self._on_success, self._on_failure)
        self._query_executer.assert_called_once()

    def test_update_cell_when_in_cache(self):
        row_id = 0
        column_index = 0
        new_value = 'Updates'

        edit_row = mock.MagicMock()

        edit_row.set_cell_value = mock.MagicMock(return_value=new_value)

        self._data_editor_session._session_cache[row_id] = edit_row
        self._data_editor_session._is_initialized = True
        self._data_editor_session._last_row_id = 10

        result = self._data_editor_session.update_cell(row_id, column_index, new_value)

        self.assertEqual(new_value, result)

    def test_create_row(self):
        '''
        Validate that create row creates new row based with new row id and returns
        CreateRowResponse
        '''
        self._data_editor_session._last_row_id = 0

        calculated_column = DbColumn()
        calculated_column.is_updatable = False
        calculated_column_metadata = EditColumnMetadata(calculated_column, None)

        default_value_column = DbColumn()
        default_value_column.data_type = 'bool'
        default_value_column.is_updatable = True
        default_value_column_metadata = EditColumnMetadata(default_value_column, '0')

        columns_metadata = [calculated_column_metadata, default_value_column_metadata]

        self._data_editor_session.table_metadata = EditTableMetadata(self._schema_name, self._table_name, columns_metadata, MYSQL_PROVIDER_NAME)

        result_set = self.get_result_set([(1, False)])

        result_set.columns_info = [calculated_column, default_value_column]

        self._data_editor_session._result_set = result_set

        self._data_editor_session._is_initialized = True
        response: CreateRowResponse = self._data_editor_session.create_row()

        self.assertEqual(1, response.new_row_id)
        self.assertEqual(len(columns_metadata), len(response.default_values))

        self.assertEqual('&lt;TBD&gt;', response.default_values[0])
        self.assertEqual('False', response.default_values[1])

    def test_create_row_not_initialized(self):
        with self.assertRaises(RuntimeError) as context_manager:
            self._data_editor_session.create_row()

        if context_manager.exception.args is not None:
            self.assertEqual("Edit session has not been initialized", context_manager.exception.args[0])

    def test_delete_row(self):
        '''
        Verify that it creates and DeleteRow and adds it to session cache
        '''
        row_id = 1
        self._data_editor_session._is_initialized = True
        self._data_editor_session.table_metadata = self._edit_table_metadata
        self._data_editor_session._last_row_id = 3

        self._data_editor_session.delete_row(row_id)

        delete_row = self._data_editor_session._session_cache.get(row_id)

        self.assertEqual(row_id, delete_row.row_id)
        self.assertEqual(None, self._data_editor_session._result_set)

    def test_delete_row_not_initialized(self):
        with self.assertRaises(RuntimeError) as context_manager:
            self._data_editor_session.delete_row(2)

        if context_manager.exception.args is not None:
            self.assertEqual("Edit session has not been initialized", context_manager.exception.args[0])

    def test_delete_row_with_rowid_out_of_range(self):
        self._data_editor_session.initialize(self._initialize_edit_request, self._connection, self._query_executer, self._on_success, self._on_failure)
        self._data_editor_session._is_initialized = True
        self._data_editor_session._last_row_id = 2
        delete_row_id = 3

        with self.assertRaises(IndexError) as context_manager:
            self._data_editor_session.delete_row(delete_row_id)

        if context_manager.exception.args is not None:
            self.assertEqual(f"Parameter row_id with value {delete_row_id} is out of range", context_manager.exception.args[0])

    def test_revert_row_when_row_exists(self):
        '''
        Verify that it removes the row from the cache
        '''
        row_id = 1

        self._data_editor_session._session_cache[row_id] = {}
        self._data_editor_session._is_initialized = True
        self._data_editor_session._last_row_id = 3

        self._data_editor_session.revert_row(row_id)

        self.assertEqual(0, len(self._data_editor_session._session_cache))

    def test_revert_row_not_initialized(self):
        with self.assertRaises(RuntimeError) as context_manager:
            self._data_editor_session.revert_row(3)

        if context_manager.exception.args is not None:
            self.assertEqual("Edit session has not been initialized", context_manager.exception.args[0])

    def test_revert_row_with_rowid_out_of_range(self):
        self._data_editor_session.initialize(self._initialize_edit_request, self._connection, self._query_executer, self._on_success, self._on_failure)
        self._data_editor_session._is_initialized = True
        self._data_editor_session._last_row_id = 2
        revert_row_id = 3

        with self.assertRaises(IndexError) as context_manager:
            self._data_editor_session.revert_row(revert_row_id)

        if context_manager.exception.args is not None:
            self.assertEqual(f"Parameter row_id with value {revert_row_id} is out of range", context_manager.exception.args[0])

    def test_revert_row_when_row_does_not_exists(self):
        '''
        Verify that it throws exception when row is not in cache
        '''
        row_id = 1
        self._data_editor_session._is_initialized = True
        self._data_editor_session._last_row_id = 3

        with self.assertRaises(KeyError):
            self._data_editor_session.revert_row(row_id)

    def test_commit_edit_fire_success(self):

        mock_edit = mock.MagicMock()
        mock_edit.row_id = 0
        row_id = 1
        success_callback = mock.MagicMock()

        script_template = 'script'
        query_params = []

        edit_script = EditScript(script_template, query_params)

        mock_edit.get_script = mock.Mock(return_value=edit_script)

        self._data_editor_session._session_cache[row_id] = mock_edit

        self._data_editor_session._result_set = self.get_result_set([(1, False)])

        self._data_editor_session._is_initialized = True
        self._data_editor_session.commit_edit(self._connection, success_callback, mock.MagicMock())
        self._data_editor_session._commit_task.join()

        self.assertTrue(len(self._data_editor_session._session_cache) == 0)

        success_callback.assert_called_once()

        mock_edit.get_script.assert_called_once()

        self._mock_cursor.mogrify.assert_called_once()

        self._mock_cursor.execute.assert_called_once_with(self._mock_cursor.mogrified_value)

        mock_edit.apply_changes.assert_called_once()

    def test_commit_edit_not_initialized(self):
        with self.assertRaises(RuntimeError):
            self._data_editor_session.commit_edit(self._connection, mock.MagicMock(), mock.MagicMock())

    def test_commit_edit_with_null_connection(self):
        self._data_editor_session.initialize(self._initialize_edit_request, self._connection, self._query_executer, self._on_success, self._on_failure)
        self._data_editor_session._is_initialized = True

        with self.assertRaises(ValueError) as context_manager:
            self._data_editor_session.commit_edit(None, mock.MagicMock(), mock.MagicMock())

        if context_manager.exception.args is not None:
            self.assertEqual(f"connection is None", context_manager.exception.args[0])

    def test_commit_edit_with_none_success_handler(self):
        self._data_editor_session.initialize(self._initialize_edit_request, self._connection, self._query_executer, self._on_success, self._on_failure)
        self._data_editor_session._is_initialized = True

        with self.assertRaises(ValueError) as context_manager:
            self._data_editor_session.commit_edit(self._connection, None, mock.MagicMock())

        if context_manager.exception.args is not None:
            self.assertEqual(f"onsuccess is None", context_manager.exception.args[0])

    def test_commit_edit_with_none_failure_handler(self):
        self._data_editor_session.initialize(self._initialize_edit_request, self._connection, self._query_executer, self._on_success, self._on_failure)
        self._data_editor_session._is_initialized = True

        with self.assertRaises(ValueError) as context_manager:
            self._data_editor_session.commit_edit(self._connection, mock.MagicMock(), None)

        if context_manager.exception.args is not None:
            self.assertEqual(f"onfailure is None", context_manager.exception.args[0])

    def test_update_cell_not_initialized(self):
        session = DataEditorSession(self._metadata_factory)
        with self.assertRaises(RuntimeError):
            session.update_cell(0, 3, 'abcd')

    def test_update_cell_with_rowid_out_of_range(self):
        self._data_editor_session.initialize(self._initialize_edit_request, self._connection, self._query_executer, self._on_success, self._on_failure)
        self._data_editor_session._is_initialized = True
        self._data_editor_session._last_row_id = 2
        current_row_id = 3

        with self.assertRaises(IndexError) as context_manager:
            self._data_editor_session.update_cell(current_row_id, 4, 'abcd')

        if context_manager.exception.args is not None:
            self.assertEqual(f"Parameter row_id with value {current_row_id} is out of range", context_manager.exception.args[0])

    def test_get_rows_when_start_index_is_equal_to_row_count(self):
        rows = []
        result_set = self.get_result_set(rows)

        self._data_editor_session._result_set = result_set

        edit_row = mock.MagicMock()

        edit_row.get_edit_row = mock.Mock(return_value=edit_row)

        self._data_editor_session._session_cache[0] = edit_row

        edit_rows = self._data_editor_session.get_rows('Test Uri', 0, 1)

        self.assertEqual(len(edit_rows), 1)
        self.assertEqual(edit_row, edit_rows[0])
        edit_row.get_edit_row.assert_called_once()

    def test_commit_when_its_a_new_row_thats_being_deleted(self):
        rows = []
        result_set = self.get_result_set(rows)

        row_delete = RowDelete(0, result_set, self._edit_table_metadata)

        row_delete.get_script = mock.Mock(return_value="Some query")

        self._data_editor_session._session_cache[0] = row_delete
        self._data_editor_session._result_set = result_set

        self._data_editor_session._is_initialized = True
        self._data_editor_session.commit_edit(self._connection, mock.MagicMock(), mock.MagicMock())
        self._data_editor_session._commit_task.join()

        row_delete.get_script.assert_not_called()
        self.assertFalse(bool(self._data_editor_session._session_cache))

    def test_commit_when_its_a_existing_row_thats_being_deleted(self):
        rows = [("Result1", 53), ("Result2", None,)]
        result_set = self.get_result_set(rows)

        script_template = 'script'
        query_params = []

        edit_script = EditScript(script_template, query_params)

        row_delete = RowDelete(0, result_set, self._edit_table_metadata)

        row_delete.get_script = mock.Mock(return_value=edit_script)

        self._data_editor_session._session_cache[0] = row_delete
        self._data_editor_session._result_set = result_set

        self._data_editor_session._is_initialized = True
        self._data_editor_session.commit_edit(self._connection, mock.MagicMock(), mock.MagicMock())
        self._data_editor_session._commit_task.join()

        row_delete.get_script.assert_called_once()
        self.assertFalse(bool(self._data_editor_session._session_cache))


if __name__ == '__main__':
    unittest.main()
