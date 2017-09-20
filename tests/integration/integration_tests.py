# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing the logic to set up integration tests with a database connection"""

import json
import os
from unittest import mock
import uuid

import psycopg2


def integration_test(test):
    """Decorator used to indicate that a test is an integration test, giving it a connection"""

    def new_test(*args):
        _ConnectionManager.current_test_is_integration_test = True
        connection = get_connection()
        connection.autocommit = True
        try:
            with mock.patch('psycopg2.connect', mock.Mock(return_value=connection)):
                test(*args)
        finally:
            _ConnectionManager.current_test_is_integration_test = False
            _ConnectionManager.close_connection()
    new_test.is_integration_test = True
    new_test.__name__ = test.__name__
    return new_test


# Indicate that nose should not treat the decorator as its own test
integration_test.__test__ = False


def get_connection():
    """Get a connection that can be used in integration tests"""
    return _ConnectionManager.get_connection()


class _ConnectionManager:
    current_test_is_integration_test = False
    _maintenance_connection = None
    _current_test_connection = None

    @classmethod
    def get_connection(cls) -> psycopg2.extensions.connection:
        if not cls.current_test_is_integration_test:
            raise RuntimeError('get_connection can only be called from tests with an integration_test decorator')
        if cls._maintenance_connection is None:
            cls._maintenance_connection = cls._open_connection()
        if cls._current_test_connection is None:
            cls._current_test_connection = cls._open_test_connection()
        return cls._current_test_connection

    @classmethod
    def close_connection(cls):
        if not cls._current_test_connection:
            return
        db_name = cls._current_test_connection.get_dsn_parameters()['dbname']
        try:
            cls._current_test_connection.close()
        except:
            pass
        cls._current_test_connection = None
        with cls._maintenance_connection.cursor() as cursor:
            cursor.execute('DROP DATABASE ' + db_name)

    @staticmethod
    def _open_connection(db_name=None) -> psycopg2.extensions.connection:
        config_file_name = 'config.json'
        current_folder = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(current_folder, config_file_name)
        if not os.path.exists(config_path):
            config_path += '.txt'
        if not os.path.exists(config_path):
            raise RuntimeError(f'No test config file found at {config_path}')
        config_dict = json.load(open(config_path))
        if db_name is not None:
            config_dict['dbname'] = db_name
        try:
            connection = psycopg2.connect(**config_dict)
            return connection
        except Exception as e:
            raise RuntimeError(f'Unable to establish a database connection for integration tests') from e

    @classmethod
    def _open_test_connection(cls) -> psycopg2.extensions.connection:
        db_name = 'test' + uuid.uuid4().hex
        with cls._maintenance_connection.cursor() as cursor:
            cursor.execute('CREATE DATABASE ' + db_name)
        return cls._open_connection(db_name)
