# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing the logic to set up integration tests with a database connection"""

import json
import os
import uuid

import psycopg2


def integration_test(test):
    """Decorator used to indicate that a test is an integration test, giving it a connection"""

    def new_test(*args):
        _ConnectionManager.current_test_is_integration_test = True
        try:
            test(*args)
        finally:
            _ConnectionManager.current_test_is_integration_test = False
            _ConnectionManager.drop_test_database()
    new_test.is_integration_test = True
    new_test.__name__ = test.__name__
    return new_test


# Indicate that nose should not treat the decorator as its own test
integration_test.__test__ = False


def get_connection_details() -> dict:
    """
    Get connection details that can be used in integration tests. These details are formatted as a
    dictionary of key-value pairs that can be passed directly to psycopg2.connect as parameters.
    """
    return _ConnectionManager.get_test_connection_details()


class _ConnectionManager:
    current_test_is_integration_test: bool = False
    _maintenance_connection: psycopg2.extensions.connection = None
    _current_test_connection_details: dict = None

    @classmethod
    def get_test_connection_details(cls):
        if not cls.current_test_is_integration_test:
            raise RuntimeError('get_connection_details can only be called from tests with an integration_test decorator')
        if not cls._current_test_connection_details:
            cls._create_test_database()
        return cls._current_test_connection_details

    @classmethod
    def _open_maintenance_connection(cls):
        details = cls._get_connection_details()
        cls._maintenance_connection = psycopg2.connect(**details)
        cls._maintenance_connection.autocommit = True

    @staticmethod
    def _get_connection_details(db_name=None) -> dict:
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
        return config_dict

    @classmethod
    def _create_test_database(cls) -> None:
        db_name = 'test' + uuid.uuid4().hex
        if cls._maintenance_connection is None:
            cls._open_maintenance_connection()
        with cls._maintenance_connection.cursor() as cursor:
            cursor.execute('CREATE DATABASE ' + db_name)
        cls._current_test_connection_details = cls._get_connection_details(db_name)

    @classmethod
    def drop_test_database(cls) -> None:
        if not cls._current_test_connection_details:
            return
        db_name = cls._current_test_connection_details['dbname']
        cls._current_test_connection_details = None
        with cls._maintenance_connection.cursor() as cursor:
            cursor.execute('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = (%s)', (db_name,))
            cursor.execute('DROP DATABASE ' + db_name)
