# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

import tests.utils as utils
from ossdbtoolsservice.query.batch import (Batch, BatchEvents,
                                           ResultSetStorageType, SelectBatch,
                                           create_batch, create_result_set)
from ossdbtoolsservice.query.contracts import (SaveResultsRequestParams,
                                               SelectionData)
from ossdbtoolsservice.query.file_storage_result_set import \
    FileStorageResultSet
from ossdbtoolsservice.query.in_memory_result_set import InMemoryResultSet
from tests.pgsmo_tests.utils import MockPGServerConnection


class TestBatch(unittest.TestCase):

    def setUp(self):
        self._cursor = utils.MockPsycopgCursor(None)
        self._connection = MockPGServerConnection(cur=self._cursor)
        self._batch_text = 'Select * from t1'
        self._batch_id = 1
        self._batch_events = BatchEvents()
        self._selection_data = SelectionData()
        self._result_set = mock.MagicMock()

    def create_batch_with(self, batch, storage_type: ResultSetStorageType):
        return batch(self._batch_text, self._batch_id, self._selection_data, self._batch_events, storage_type)

    def create_and_execute_batch(self, batch):
        with mock.patch('ossdbtoolsservice.query.batch.create_result_set', new=mock.Mock(return_value=self._result_set)):
            batch = self.create_batch_with(batch, ResultSetStorageType.IN_MEMORY)
            batch.execute(self._connection)
            return batch

    def assert_properties(self, property_name: str, expected_value):
        batch = self.create_and_execute_batch(Batch)

        self.assertEqual(getattr(batch, property_name), expected_value)

    def test_execute_calls_execute_on_cursor(self):
        self.create_and_execute_batch(Batch)
        self._cursor.execute.assert_called_once_with(self._batch_text)

    def test_execute_calls_read_result_to_end_on_result_set(self):
        batch = self.create_and_execute_batch(Batch)

        self.assertEqual(batch._result_set, self._result_set)
        self._result_set.read_result_to_end.assert_called_once_with(self._cursor)

    def test_execute_sets_has_executed(self):
        batch = self.create_and_execute_batch(Batch)

        self.assertTrue(batch._has_executed)

    def test_select_batch_creates_server_side_cursor(self):
        cursor_name = 'Test'
        with mock.patch('uuid.uuid4', new=mock.Mock(return_value=cursor_name)):
            self.create_and_execute_batch(SelectBatch)

        self._connection.cursor.assert_called_once_with(name=cursor_name, withhold=True)

    def test_prop_batch_summary(self):
        batch_summary = mock.MagicMock()

        with mock.patch('ossdbtoolsservice.query.contracts.BatchSummary.from_batch', new=mock.Mock(return_value=batch_summary)):
            self.assert_properties('batch_summary', batch_summary)

    def test_prop_has_error(self):
        self.assert_properties('has_error', False)

    def test_prop_has_executed(self):
        self.assert_properties('has_executed', True)

    def test_create_result_set_with_type_in_memory(self):
        result_set = create_result_set(ResultSetStorageType.IN_MEMORY, 1, 1)

        self.assertTrue(isinstance(result_set, InMemoryResultSet))

    def test_create_result_set_with_type_file_storage(self):
        result_set = create_result_set(ResultSetStorageType.FILE_STORAGE, 1, 1)

        self.assertTrue(isinstance(result_set, FileStorageResultSet))

    def test_create_batch_for_select(self):

        batch_text = ''' Select
        * from t1 '''

        batch = create_batch(batch_text, 0, self._selection_data, self._batch_events, ResultSetStorageType.IN_MEMORY)

        self.assertTrue(isinstance(batch, SelectBatch))

    def test_create_batch_for_select_with_additional_spaces(self):

        batch_text = '    Select    *      from t1 '

        batch = create_batch(batch_text, 0, self._selection_data, self._batch_events, ResultSetStorageType.IN_MEMORY)

        self.assertTrue(isinstance(batch, SelectBatch))

    def test_create_batch_for_select_into(self):

        batch_text = '    Select   into  temptable  from t1 '

        batch = create_batch(batch_text, 0, self._selection_data, self._batch_events, ResultSetStorageType.IN_MEMORY)

        self.assertFalse(isinstance(batch, SelectBatch))
        self.assertTrue(isinstance(batch, Batch))

    def test_create_batch_for_non_select(self):

        batch_text = 'Insert into t1 values(1)'

        batch = create_batch(batch_text, 0, self._selection_data, self._batch_events, ResultSetStorageType.IN_MEMORY)

        self.assertFalse(isinstance(batch, SelectBatch))
        self.assertTrue(isinstance(batch, Batch))

    def test_get_subset(self):
        expected_subset = []
        batch = create_batch('select 1', 0, self._selection_data, self._batch_events, ResultSetStorageType.IN_MEMORY)
        self._result_set.get_subset = mock.Mock(return_value=expected_subset)

        batch._result_set = self._result_set

        subset = batch.get_subset(0, 10)

        self.assertEqual(expected_subset, subset)
        self._result_set.get_subset.assert_called_once_with(0, 10)

    def test_batch_calls_close_on_cursor_when_executed(self):
        self.create_and_execute_batch(Batch)

        self._cursor.close.assert_called_once()

    def test_save_as(self):
        batch = self.create_and_execute_batch(Batch)

        params = SaveResultsRequestParams()
        params.result_set_index = 0

        file_factory = mock.MagicMock()
        on_success = mock.MagicMock()
        on_error = mock.MagicMock()

        result_set_save_as_mock = mock.MagicMock()
        batch._result_set.save_as = result_set_save_as_mock

        batch.save_as(params, file_factory, on_success, on_error)

        result_set_save_as_mock.assert_called_once_with(params, file_factory, on_success, on_error)

    def test_save_as_with_invalid_batch_index(self):
        batch = self.create_and_execute_batch(Batch)
        params = SaveResultsRequestParams()
        params.result_set_index = 1

        with self.assertRaises(IndexError) as context_manager:
            batch.save_as(params, None, None, None)
            self.assertEquals('Result set index should be always 0', context_manager.exception.args[0])


if __name__ == '__main__':
    unittest.main()
