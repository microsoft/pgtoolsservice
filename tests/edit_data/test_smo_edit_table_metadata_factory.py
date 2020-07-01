# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import unittest
from unittest import mock

from ossdbtoolsservice.edit_data import SmoEditTableMetadataFactory
from tests.utils import MockConnection
from pgsmo import Server, Table, View, Column


class TestSmoEditTableMetadataFactory(unittest.TestCase):

    def setUp(self):
        self._smo_metadata_factory = SmoEditTableMetadataFactory()
        self._connection = MockConnection({"port": "8080", "host": "test", "dbname": "test", "user": "test"})
        self._server = Server(self._connection)
        self._schema_name = 'public'
        self._table_name = 'Employee'
        self._view_name = 'Vendor'
        self._table_object_type = 'TABLE'
        self._view_object_type = 'VIEW'
        self._columns = [Column(self._server, "testTable", 'testName', 'testDatatype')]

    def test_get_with_table_type(self):
        table = Table(self._server, None, self._table_name)
        table._columns = self._columns

        with mock.patch('ossdbtoolsservice.utils.object_finder.find_table', new=mock.Mock(return_value=table)):
            metadata = self._smo_metadata_factory.get(self._connection, self._schema_name, self._table_name, self._table_object_type)
            self.assertEqual(len(metadata.columns_metadata), len(table.columns))

    def test_get_with_view_type(self):
        view = View(self._server, None, self._view_name)
        view._columns = self._columns

        with mock.patch('ossdbtoolsservice.utils.object_finder.find_view', new=mock.Mock(return_value=view)):
            metadata = self._smo_metadata_factory.get(self._connection, self._schema_name, self._view_name, self._view_object_type)
            self.assertEqual(len(metadata.columns_metadata), len(view.columns))

    def test_get_with_other_type_raises_exception(self):

        with self.assertRaises(Exception):
            self._smo_metadata_factory.get(self._connection, self._schema_name, self._view_name, 'Other')


if __name__ == '__main__':
    unittest.main()
