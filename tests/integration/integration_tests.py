# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing the logic to set up integration tests with a database connection"""

import functools
import json
import os
import uuid

import psycopg


def integration_test(min_version=None, max_version=None):
    """
    Decorator used to indicate that a test is an integration test, giving it a connection

    :param min_version: The minimum server version, as an integer,
        for running the test (e.g. 90600 for 9.6.0)
    :param max_version: The maximum server version, as an integer,
        for running the test (e.g. 90600 for 9.6.0)
    """

    # If the decorator is called without parentheses,
    # the first argument will actually be the test function
    test_function = None
    if callable(min_version):
        test_function = min_version
        min_version = None

    def integration_test_internal(test):
        @functools.wraps(test)
        def new_test(*args):
            _ConnectionManager.current_test_is_integration_test = True
            try:
                _ConnectionManager.run_test(test, min_version, max_version, *args)
            finally:
                _ConnectionManager.current_test_is_integration_test = False
                _ConnectionManager.drop_test_databases()

        new_test.is_integration_test = True
        new_test.__name__ = test.__name__
        return new_test

    return (
        integration_test_internal
        if test_function is None
        else integration_test_internal(test_function)
    )


def get_connection_details() -> dict:
    """
    Get connection details that can be used in integration tests.
    These details are formatted as a
    dictionary of key-value pairs that can be passed
    directly to psycopg.connect as parameters.
    """
    return _ConnectionManager.get_test_connection_details()


def create_extra_test_database() -> str:
    """
    Create an extra database for the current test and return its name. The database will
    automatically be dropped at the end of the test.
    """
    return _ConnectionManager.create_extra_database()


# Indicate that nose should not treat these functions as their own tests
integration_test.__test__ = False
create_extra_test_database.__test__ = False


class _ConnectionManager:
    current_test_is_integration_test: bool = False
    _maintenance_connections: list[psycopg.Connection] = []
    _current_test_connection_detail_list: list[dict] = None
    _in_progress_test_index: int = None
    _extra_databases: list[str] = []

    @classmethod
    def get_test_connection_details(cls):
        if not cls.current_test_is_integration_test or cls._in_progress_test_index is None:
            raise RuntimeError(
                "get_connection_details can only be called "
                "from tests with an integration_test decorator"
            )
        # Return a copy of the test connection details dictionary
        return dict(cls._current_test_connection_detail_list[cls._in_progress_test_index])

    @classmethod
    def create_extra_database(cls) -> str:
        maintenance_connection = cls._maintenance_connections[cls._in_progress_test_index]
        db_name = "test" + uuid.uuid4().hex
        with maintenance_connection.cursor() as cursor:
            cursor.execute("CREATE DATABASE " + db_name)
        cls._extra_databases.append(db_name)
        return db_name

    @classmethod
    def run_test(cls, test, min_version, max_version, *args):
        cls._create_test_databases()
        needs_setup = False
        for index, details in enumerate(cls._current_test_connection_detail_list):
            cls._in_progress_test_index = index
            server_version = cls._maintenance_connections[index].info.server_version
            if (
                min_version is not None
                and server_version < min_version
                or max_version is not None
                and server_version > max_version
            ):
                continue
            try:
                if needs_setup:
                    args[0].setUp()
                test(*args)
                args[0].tearDown()
                needs_setup = True
            except Exception as e:
                host = details["host"]
                server_version = cls._maintenance_connections[index].info.server_version
                raise RuntimeError(
                    f"Test failed while executing on server {index + 1} "
                    f"(host: {host}, version: {server_version})"
                ) from e

    @classmethod
    def _open_maintenance_connections(cls):
        config_list = cls._get_connection_configurations()
        cls._maintenance_connections = []
        cls._current_test_connection_detail_list = []
        for config_dict in config_list:
            connection = psycopg.connect(**config_dict)
            cls._maintenance_connections.append(connection)
            connection.autocommit = True
            config_dict["dbname"] = None
            cls._current_test_connection_detail_list.append(config_dict)

    @staticmethod
    def _get_connection_configurations() -> dict:
        config_file_name = "config.json"
        current_folder = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(current_folder, config_file_name)
        if not os.path.exists(config_path):
            config_path += ".txt"

        if not os.path.exists(config_path):
            raise RuntimeError(f"No test config file found at {config_path}")

        with open(config_path, encoding="utf-8-sig") as f:
            json_content = f.read()
            config_list = json.loads(json_content)

        if not isinstance(config_list, list):
            config_list = [config_list]

        return config_list

    @classmethod
    def _create_test_databases(cls) -> None:
        db_name = "test" + uuid.uuid4().hex
        if not cls._maintenance_connections:
            cls._open_maintenance_connections()
        for index, connection in enumerate(cls._maintenance_connections):
            with connection.cursor() as cursor:
                cursor.execute("CREATE DATABASE " + db_name)
            cls._current_test_connection_detail_list[index]["dbname"] = db_name

    @classmethod
    def drop_test_databases(cls) -> None:
        if not cls._current_test_connection_detail_list:
            return
        for index, details in enumerate(cls._current_test_connection_detail_list):
            try:
                db_name = details["dbname"]
                with cls._maintenance_connections[index].cursor() as cursor:
                    cls._drop_database(db_name, cursor)
                    for extra_db_name in cls._extra_databases:
                        cls._drop_database(extra_db_name, cursor)
                    cls._extra_databases = []
            except Exception:
                pass
        for details in cls._current_test_connection_detail_list:
            details["dbname"] = None

    @staticmethod
    def _drop_database(db_name, cursor):
        try:
            cursor.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = (%s)",
                (db_name,),
            )
            cursor.execute("DROP DATABASE " + db_name)
        except Exception as e:
            raise RuntimeError(f"Failed to drop database {db_name}") from e
