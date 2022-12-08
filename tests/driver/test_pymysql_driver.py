# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock
from ossdbtoolsservice.driver.types.pymysql_driver import MySQLConnection
from ossdbtoolsservice.utils import constants

from tests.utils import MockPyMySQLCursor, MockPyMySQLConnection


class TestMySQLConnection(unittest.TestCase):
    """Methods for testing the MySQL Connection"""

    def setUp(self):
        """Set up the tests with a mysql connection"""

        mock_cursor = MockPyMySQLCursor([['5.7.29-log']])
        # Set up the mock connection for pymysql's connect method to return
        self.mock_pymysql_connection = MockPyMySQLConnection(cursor=mock_cursor)

    def test_mysql_connection_ssl_enable(self):
        """Test creating mysql connection with ssl enabled"""

        mysql_connection_params = {
            'connectTimeout': '30',
            'dbname': '',
            'groupId': 'C777F06B-202E-4480-B475-FA416154D458',
            'host': 'mysql-test.mysql.database.azure.com',
            'password': 'samplePass123',
            'user': 'sampleUser',
            'ssl': 'require',
            'ssl.ca': 'path_to_ssl_cert'
        }

        with mock.patch('pymysql.connect', new=mock.Mock(return_value=self.mock_pymysql_connection)):
            mysqlConnection = MySQLConnection(mysql_connection_params)

        expected_connection_options = {
            'connect_timeout': 30,
            'database': '',
            'host': 'mysql-test.mysql.database.azure.com',
            'password': 'samplePass123',
            'port': 3306,
            'user': 'sampleUser',
            'ssl': {'ca': None, 'check_hostname': False, 'verify_mode': 'none'}
        }
        print(mysqlConnection.connection_options)
        self.assertDictEqual(mysqlConnection.connection_options, expected_connection_options)
        self.assertIs(mysqlConnection.connection, self.mock_pymysql_connection)
        self.assertTrue(mysqlConnection.autocommit)
        self.assertEqual(mysqlConnection.default_database, constants.DEFAULT_DB[constants.MYSQL_PROVIDER_NAME])

    def test_mysql_connection_ssl_disable(self):
        """Test creating mysql connection with ssl disabled"""

        mysql_connection_params = {
            'connectTimeout': '30',
            'dbname': '',
            'groupId': 'C777F06B-202E-4480-B475-FA416154D458',
            'host': 'mysql-test.mysql.database.azure.com',
            'password': 'samplePass123',
            'user': 'sampleUser'}

        with mock.patch('pymysql.connect', new=mock.Mock(return_value=self.mock_pymysql_connection)):
            mysqlConnection = MySQLConnection(mysql_connection_params)

        expected_connection_options = {
            'connect_timeout': 30,
            'database': '',
            'host': 'mysql-test.mysql.database.azure.com',
            'password': 'samplePass123',
            'port': 3306,
            'user': 'sampleUser',
            'ssl': {'ca': None, 'check_hostname': False, 'verify_mode': 'none'}}
        print(mysqlConnection.connection_options)
        self.assertDictEqual(mysqlConnection.connection_options, expected_connection_options)
        self.assertIs(mysqlConnection.connection, self.mock_pymysql_connection)
        self.assertTrue(mysqlConnection.autocommit)
        self.assertEqual(mysqlConnection.default_database, constants.DEFAULT_DB[constants.MYSQL_PROVIDER_NAME])

    def test_mysql_connection_port_provided(self):
        """Test creating mysql connection with dbname provided"""

        mysql_connection_params = {
            'connectTimeout': '30',
            'dbname': '',
            'groupId': 'C777F06B-202E-4480-B475-FA416154D458',
            'host': 'mysql-test.mysql.database.azure.com',
            'password': 'samplePass123',
            'user': 'sampleUser',
            'port': 3307}

        with mock.patch('pymysql.connect', new=mock.Mock(return_value=self.mock_pymysql_connection)):
            mysqlConnection = MySQLConnection(mysql_connection_params)

        expected_connection_options = {
            'connect_timeout': 30,
            'database': '',
            'host': 'mysql-test.mysql.database.azure.com',
            'password': 'samplePass123',
            'port': 3307,
            'user': 'sampleUser',
            'ssl': {'ca': None, 'check_hostname': False, 'verify_mode': 'none'}}
        print(mysqlConnection.connection_options)
        self.assertDictEqual(mysqlConnection.connection_options, expected_connection_options)
        self.assertIs(mysqlConnection.connection, self.mock_pymysql_connection)
        self.assertTrue(mysqlConnection.autocommit)
        self.assertEqual(mysqlConnection.default_database, constants.DEFAULT_DB[constants.MYSQL_PROVIDER_NAME])

    def test_mysql_connection_dbname_provided(self):
        """Test creating mysql connection with dbname provided"""

        mysql_connection_params = {
            'connectTimeout': '30',
            'dbname': 'mysql',
            'groupId': 'C777F06B-202E-4480-B475-FA416154D458',
            'host': 'mysql-test.mysql.database.azure.com',
            'password': 'samplePass123',
            'user': 'sampleUser'}

        with mock.patch('pymysql.connect', new=mock.Mock(return_value=self.mock_pymysql_connection)):
            mysqlConnection = MySQLConnection(mysql_connection_params)

        expected_connection_options = {
            'connect_timeout': 30,
            'database': 'mysql',
            'host': 'mysql-test.mysql.database.azure.com',
            'password': 'samplePass123',
            'port': 3306,
            'user': 'sampleUser',
            'ssl': {'ca': None, 'check_hostname': False, 'verify_mode': 'none'}}
        print(mysqlConnection.connection_options)
        self.assertDictEqual(mysqlConnection.connection_options, expected_connection_options)
        self.assertIs(mysqlConnection.connection, self.mock_pymysql_connection)
        self.assertTrue(mysqlConnection.autocommit)
        self.assertEqual(mysqlConnection.default_database, constants.DEFAULT_DB[constants.MYSQL_PROVIDER_NAME])


if __name__ == '__main__':
    unittest.main()
