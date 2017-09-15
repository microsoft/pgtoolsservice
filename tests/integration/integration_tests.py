# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing the logic to set up integration tests with a database connection"""

import json
import os
from unittest import mock

import psycopg2


def integration_test(auto_cleanup=True):
    """
    Decorator used to mock psycopg2.connect in integration tests

    :param auto_cleanup: True if all SQL executed by the connection should be done in a single
    transaction and rolled back at the end of the test, False to indicate that the test's author
    will manually clean up any changes to the database made by their test
    """

    def internal_decorator(test):
        def new_test(*args):
            _ConnectionManager.current_test_is_integration_test = True
            connection = get_connection()
            connection.autocommit = not auto_cleanup
            try:
                with mock.patch('psycopg2.connect', mock.Mock(return_value=connection)):
                    test(*args)
            finally:
                _ConnectionManager.current_test_is_integration_test = False
                if auto_cleanup:
                    connection.rollback()
                elif connection.get_transaction_status() is not psycopg2.extensions.TRANSACTION_STATUS_IDLE:
                    # Then a non auto_cleanup test failed to clean up. Roll back the transaction so other tests might continue
                    connection.cursor().execute('ROLLBACK')
                    raise RuntimeError('The test did not clean up its database modifications. This can cause other tests to fail!')
        new_test.is_integration_test = True
        return new_test

    # If the parameter is a function (i.e. the decorated test) instead of a boolean then the
    # decorator was called without parentheses, so apply the decorator directly to the test
    if callable(auto_cleanup):
        return internal_decorator(auto_cleanup)

    # Otherwise return a function that will take the test as a parameter
    return internal_decorator


# Indicate that nose should not treat the decorator as its own test
integration_test.__test__ = False


def get_connection():
    """Get a connection that can be used in integration tests"""
    return _ConnectionManager.get_connection()


class _ConnectionManager:
    current_test_is_integration_test = False
    _connection = None

    @classmethod
    def get_connection(cls) -> psycopg2.extensions.connection:
        if not cls.current_test_is_integration_test:
            raise RuntimeError('get_connection can only be called from tests with an integration_test decorator')
        if cls._connection is None:
            cls._connection = cls._open_test_connection()
        return cls._connection

    @staticmethod
    def _open_test_connection() -> psycopg2.extensions.connection:
        config_file_name = 'config.json'
        current_folder = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(current_folder, config_file_name)
        if not os.path.exists(config_path):
            config_path += '.txt'
        if not os.path.exists(config_path):
            raise RuntimeError(f'No test config file found at {config_path}')
        config_dict = json.load(open(config_path))
        try:
            return psycopg2.connect(**config_dict)
        except Exception as e:
            raise RuntimeError(f'Unable to establish a database connection for integration tests') from e
