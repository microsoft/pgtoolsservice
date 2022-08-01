# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing the logic to set up integration tests with a database connection"""

import functools
import json
import os
from typing import List
from ossdbtoolsservice.utils.constants import MARIADB_PROVIDER_NAME, MYSQL_PROVIDER_NAME, PG_PROVIDER_NAME

from tests.integration.connections_for_integration_tests import PostgreSQLConnection

INTEGRATION_TEST_SUPPORTED_PROVIDERS = [PG_PROVIDER_NAME]

CONNECTORS = {
    PG_PROVIDER_NAME: PostgreSQLConnection,
    MYSQL_PROVIDER_NAME: None,
    MARIADB_PROVIDER_NAME: None
}


def integration_test(min_version=None, max_version=None, provider=PG_PROVIDER_NAME):
    """
    Decorator used to indicate that a test is an integration test, giving it a connection

    :param min_version: The minimum server version, as an integer, for running the test (e.g. 90600 for 9.6.0)
    :param max_version: The maximum server version, as an integer, for running the test (e.g. 90600 for 9.6.0)
    :param provider: connection provider
    """
    # If the provider is not supported in integration test, raise exception
    if(provider not in INTEGRATION_TEST_SUPPORTED_PROVIDERS):
        print("Provider is : " + provider)
        raise RuntimeError('Provider not supported for integration tests')

    # If the decorator is called without parentheses, the first argument will actually be the test function
    test_function = None
    if callable(min_version):
        test_function = min_version
        min_version = None

    def integration_test_internal(test):
        @functools.wraps(test)
        def new_test(*args):
            _ConnectionManager.current_test_is_integration_test = True
            try:
                _ConnectionManager.run_test(test, provider, min_version, max_version, *args)
            finally:
                _ConnectionManager.current_test_is_integration_test = False
        new_test.is_integration_test = True
        new_test.__name__ = test.__name__
        return new_test

    return integration_test_internal if test_function is None else integration_test_internal(test_function)


def get_connection_details() -> dict:
    """
    Get connection details that can be used in integration tests. These details are formatted as a
    dictionary of key-value pairs that can be passed directly to psycopg2.connect as parameters.
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
    _current_test_connection_detail_list: List[dict] = None
    _in_progress_test_index: int = None
    _extra_databases: List[str] = []

    @classmethod
    def get_test_connection_details(cls):
        if not cls.current_test_is_integration_test or cls._in_progress_test_index is None:
            raise RuntimeError('get_connection_details can only be called from tests with an integration_test decorator')
        # Return a copy of the test connection details dictionary
        return dict(cls._current_test_connection_detail_list[cls._in_progress_test_index])

    @classmethod
    def create_extra_database(cls) -> str:
        db_name = 'flexibleserverdb'
        cls._extra_databases.append(db_name)
        return db_name

    @classmethod
    def run_test(cls, test, provider, min_version, max_version, *args):
        if(cls._current_test_connection_detail_list is None):
            cls._current_test_connection_detail_list = cls._get_connection_configurations(provider)
            CONNECTORS[provider].open_connections(cls._current_test_connection_detail_list)
        cls._create_test_databases()
        needs_setup = False
        for index, details in enumerate(cls._current_test_connection_detail_list):
            cls._in_progress_test_index = index
            server_version = CONNECTORS[provider].get_connection_server_version(index)
            if min_version is not None and server_version < min_version or max_version is not None and server_version > max_version:
                continue
            try:
                if needs_setup:
                    args[0].setUp()
                test(*args)
                args[0].tearDown()
                needs_setup = True
            except Exception as e:
                host = details['host']
                server_version = CONNECTORS[provider].get_connection_server_version(index)
                raise RuntimeError(
                    f'Test failed for provider {provider} while executing on server {index + 1} (host: {host}, version: {server_version})') from e

    @staticmethod
    def _get_connection_configurations(provider) -> dict:
        config_file_name = "config.json"
        current_folder = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(current_folder, config_file_name)
        if not os.path.exists(config_path):
            config_path += '.txt'
        if not os.path.exists(config_path):
            raise RuntimeError(f'No test config file found at {config_path}')
        with open(config_path, 'rb') as config_file:
            config = json.load(config_file)
        provider_config_list = config[provider]
        if not provider_config_list:
            raise RuntimeError(f'No configuration found for provider {provider} in test config file found at {config_path}')
        return provider_config_list

    @classmethod
    def _create_test_databases(cls) -> None:
        for connection_detail in cls._current_test_connection_detail_list:
            connection_detail['dbname'] = 'flexibleserverdb'
