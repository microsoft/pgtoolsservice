# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing the logic to set up integration tests with a database connection"""

import json
import os
from typing import List
import uuid

import psycopg2


def integration_test(test):
    """Decorator used to indicate that a test is an integration test, giving it a connection"""

    def new_test(*args):
        _ConnectionManager.current_test_is_integration_test = True
        try:
            _ConnectionManager.run_test(test, *args)
        finally:
            _ConnectionManager.current_test_is_integration_test = False
            _ConnectionManager.drop_test_databases()
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
    _maintenance_connections: List[psycopg2.extensions.connection] = []
    _current_test_connection_detail_list: List[dict] = None
    _in_progress_test_connection_details: dict = None

    @classmethod
    def get_test_connection_details(cls):
        if not cls.current_test_is_integration_test or not cls._in_progress_test_connection_details:
            raise RuntimeError('get_connection_details can only be called from tests with an integration_test decorator')
        # Return a copy of the test connection details dictionary
        return dict(cls._in_progress_test_connection_details)

    @classmethod
    def run_test(cls, test, *args):
        cls._create_test_databases()
        needs_setup = False
        for index, details in enumerate(cls._current_test_connection_detail_list):
            cls._in_progress_test_connection_details = details
            try:
                if needs_setup:
                    args[0].setUp()
                test(*args)
                needs_setup = True
            except Exception as e:
                host = details['host']
                server_version = cls._maintenance_connections[index].server_version
                raise RuntimeError(f'Test failed while executing on server {index + 1} (host: {host}, version: {server_version})') from e

    @classmethod
    def _open_maintenance_connections(cls):
        config_list = cls._get_connection_configurations()
        cls._maintenance_connections = []
        cls._current_test_connection_detail_list = []
        for config_dict in config_list:
            connection = psycopg2.connect(**config_dict)
            cls._maintenance_connections.append(connection)
            connection.autocommit = True
            config_dict['dbname'] = None
            cls._current_test_connection_detail_list.append(config_dict)

    @staticmethod
    def _get_connection_configurations() -> dict:
        config_file_name = 'config.json'
        current_folder = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(current_folder, config_file_name)
        if not os.path.exists(config_path):
            config_path += '.txt'
        if not os.path.exists(config_path):
            raise RuntimeError(f'No test config file found at {config_path}')
        config_list = json.load(open(config_path))
        if not isinstance(config_list, list):
            config_list = [config_list]
        return config_list

    @classmethod
    def _create_test_databases(cls) -> None:
        db_name = 'test' + uuid.uuid4().hex
        if not cls._maintenance_connections:
            cls._open_maintenance_connections()
        for index, connection in enumerate(cls._maintenance_connections):
            with connection.cursor() as cursor:
                cursor.execute('CREATE DATABASE ' + db_name)
            cls._current_test_connection_detail_list[index]['dbname'] = db_name

    @classmethod
    def drop_test_databases(cls) -> None:
        if not cls._current_test_connection_detail_list:
            return
        for index, details in enumerate(cls._current_test_connection_detail_list):
            try:
                db_name = details['dbname']
                with cls._maintenance_connections[index].cursor() as cursor:
                    cursor.execute('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = (%s)', (db_name,))
                    cursor.execute('DROP DATABASE ' + db_name)
            except Exception:
                pass
        for details in cls._current_test_connection_detail_list:
            details['dbname'] = None
