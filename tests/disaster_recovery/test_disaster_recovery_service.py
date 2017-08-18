# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test the disaster recovery service"""

import os.path
import sys
import unittest
from unittest import mock

from pgsqltoolsservice.connection import ConnectionInfo, ConnectionService
from pgsqltoolsservice.connection.contracts import ConnectionDetails
from pgsqltoolsservice.disaster_recovery import disaster_recovery_service, DisasterRecoveryService
from pgsqltoolsservice.disaster_recovery.contracts.backup import BackupParams
from pgsqltoolsservice.tasks import TaskStatus
from pgsqltoolsservice.utils import constants
from tests import utils


class TestDisasterRecoveryService(unittest.TestCase):
    """Methods for testing the disaster recovery service"""

    def setUp(self):
        """Set up the tests with a disaster recovery service and connection service with mock connection info"""
        self.disaster_recovery_service = DisasterRecoveryService()
        self.connection_service = ConnectionService()
        self.disaster_recovery_service._service_provider = utils.get_mock_service_provider({constants.CONNECTION_SERVICE_NAME: self.connection_service})

        # Create connection information for use in the tests
        self.connection_details = ConnectionDetails()
        self.host = 'test_host'
        self.dbname = 'test_db'
        self.username = 'user'
        self.connection_details.options = {
            'host': self.host,
            'dbname': self.dbname,
            'user': self.username
        }
        self.test_uri = 'test_uri'
        self.connection_info = ConnectionInfo(self.test_uri, self.connection_details)

        # Create backup parameters for the tests
        self.request_context = utils.MockRequestContext()
        self.backup_path = 'mock/pg_dump'
        self.backup_type = 'sql'
        self.data_only = False
        self.no_owner = True
        self.schema = 'test_schema'
        self.params = BackupParams.from_dict({
            'ownerUri': self.test_uri,
            'backupInfo': {
                'type': self.backup_type,
                'path': self.backup_path,
                'data_only': self.data_only,
                'no_owner': self.no_owner,
                'schema': self.schema
            }
        })

    def test_get_pg_exe_path_local(self):
        """Test the get_pg_exe_path function when the service is running from source code"""
        # Back up these values so that the test can overwrite them
        old_arg0 = sys.argv[0]
        old_platform = sys.platform
        try:
            with mock.patch('os.path.exists', new=mock.Mock(return_value=True)):
                # Override sys.argv[0] to simulate running the code directly from source
                sys.argv[0] = os.path.normpath('/pgsqltoolsservice/pgsqltoolsservice/pgtoolsservice_main.py')

                # If I get the executable path on Mac
                sys.platform = 'darwin'
                path = disaster_recovery_service._get_pg_exe_path('pg_dump')
                # Then the path uses the mac directory and does not have a trailing .exe
                self.assertEqual(path, os.path.normpath('/pgsqltoolsservice/pgsqltoolsservice/pg_exes/mac/bin/pg_dump'))

                # If I get the executable path on Linux
                sys.platform = 'linux'
                path = disaster_recovery_service._get_pg_exe_path('pg_dump')
                # Then the path uses the linux directory and does not have a trailing .exe
                self.assertEqual(path, os.path.normpath('/pgsqltoolsservice/pgsqltoolsservice/pg_exes/linux/bin/pg_dump'))

                # If I get the executable path on Windows
                sys.platform = 'win32'
                path = disaster_recovery_service._get_pg_exe_path('pg_dump')
                # Then the path uses the win directory and does have a trailing .exe
                self.assertEqual(path, os.path.normpath('/pgsqltoolsservice/pgsqltoolsservice/pg_exes/win/pg_dump.exe'))
        finally:
            sys.argv[0] = old_arg0
            sys.platform = old_platform

    def test_get_pg_exe_path_frozen(self):
        """Test the get_pg_exe_path function when the service is running from a cx_freeze build"""
        # Back up these values so that the test can overwrite them
        old_arg0 = sys.argv[0]
        old_platform = sys.platform
        try:
            with mock.patch('os.path.exists', new=mock.Mock(return_value=True)):
                # Override sys.argv[0] to simulate running the code from a cx_freeze build
                sys.argv[0] = os.path.normpath('/pgsqltoolsservice/build/pgtoolsservice/pgtoolsservice_main')

                # If I get the executable path on Mac
                sys.platform = 'darwin'
                path = disaster_recovery_service._get_pg_exe_path('pg_dump')
                # Then the path uses the mac directory and does not have a trailing .exe
                self.assertEqual(path, os.path.normpath('/pgsqltoolsservice/build/pgtoolsservice/pg_exes/mac/bin/pg_dump'))

                # If I get the executable path on Linux
                sys.platform = 'linux'
                path = disaster_recovery_service._get_pg_exe_path('pg_dump')
                # Then the path uses the linux directory and does not have a trailing .exe
                self.assertEqual(path, os.path.normpath('/pgsqltoolsservice/build/pgtoolsservice/pg_exes/linux/bin/pg_dump'))

                # If I get the executable path on Windows
                sys.platform = 'win32'
                path = disaster_recovery_service._get_pg_exe_path('pg_dump')
                # Then the path uses the win directory and does have a trailing .exe
                self.assertEqual(path, os.path.normpath('/pgsqltoolsservice/build/pgtoolsservice/pg_exes/win/pg_dump.exe'))
        finally:
            sys.argv[0] = old_arg0
            sys.platform = old_platform

    def test_get_pg_exe_path_does_not_exist(self):
        """Test that the get_pg_exe_path function throws an error if the executable being searched for does not exist"""
        with mock.patch('os.path.exists', new=mock.Mock(return_value=False)), self.assertRaises(ValueError):
            disaster_recovery_service._get_pg_exe_path('not_pg_dump')

    def test_perform_backup(self):
        """Test that the perform_backup method passes the correct parameters to pg_dump"""
        mock_pg_path = 'mock/pg_dump'
        mock_process = mock.Mock()
        mock_process.returncode = 0
        mock_process.communicate = mock.Mock(return_value=(b'', b''))
        with mock.patch('pgsqltoolsservice.disaster_recovery.disaster_recovery_service._get_pg_exe_path',
                        new=mock.Mock(return_value=mock_pg_path)) as mock_get_path, \
                mock.patch('subprocess.Popen', new=mock.Mock(return_value=mock_process)) as mock_popen:
            # If I perform a backup
            task_result = disaster_recovery_service._perform_backup(self.connection_info, self.params)
            # Then the code got the path of pg_dump
            mock_get_path.assert_called_once_with('pg_dump')
            # And ran the pg_dump executable as a subprocess
            mock_popen.assert_called_once()
            # And then called communicate on the process
            mock_process.communicate.assert_called_once_with(b'')
            # And the arguments for the subprocess.Popen call were the expected values
            expected_args = [
                f'--file={self.backup_path}',
                '--format=p',
                f'--dbname={self.dbname}',
                f'--host={self.host}',
                f'--username={self.username}',
                '--no-owner',
                f'--schema={self.schema}'
            ]
            actual_args = mock_popen.call_args[0][0]
            self.assertEqual(actual_args[0], mock_pg_path)
            pg_dump_flags = actual_args[1:]
            for expected_arg in expected_args:
                self.assertIn(expected_arg, pg_dump_flags)
            self.assertEqual(len(expected_args), len(pg_dump_flags))
            # And the task returns a successful result
            self.assertIs(task_result.status, TaskStatus.SUCCEEDED)

    def test_perform_backup_fails(self):
        """Test that the perform_backup method handles failures by recording pg_dump's stderr output and marking the task failed"""
        mock_pg_path = 'mock/pg_dump'
        mock_process = mock.Mock()
        mock_process.returncode = 1
        test_error_message = b'test error message'
        mock_process.communicate = mock.Mock(return_value=(b'', test_error_message))
        with mock.patch('pgsqltoolsservice.disaster_recovery.disaster_recovery_service._get_pg_exe_path',
                        new=mock.Mock(return_value=mock_pg_path)), mock.patch('subprocess.Popen', new=mock.Mock(return_value=mock_process)):
            # If I perform a backup where pg_dump fails
            task_result = disaster_recovery_service._perform_backup(self.connection_info, self.params)
            # Then the task returns a failed result
            self.assertIs(task_result.status, TaskStatus.FAILED)
            # And the task contains the error message from pg_dump's stderr
            self.assertEqual(task_result.error_message, str(test_error_message, 'utf-8'))

    def test_perform_backup_no_exe(self):
        """Test that the perform_backup task fails when the pg_dump exe is not found"""
        with mock.patch('os.path.exists', new=mock.Mock(return_value=False)), mock.patch('subprocess.Popen') as mock_popen:
            # If I perform a backup when the pg_dump executable cannot be found
            task_result = disaster_recovery_service._perform_backup(self.connection_info, self.params)
            # Then the task fails and does try to kick off a new process
            self.assertIs(task_result.status, TaskStatus.FAILED)
            mock_popen.assert_not_called()

    def test_handle_backup_request(self):
        """Test that the backup request handler responds properly and kicks off a task to perform the backup"""
        # Set up the connection service to return the test's connection information
        self.connection_service.owner_to_connection_map[self.test_uri] = self.connection_info
        # Set up a mock task so that the backup code does not actually run in a separate thread
        mock_task = mock.Mock()
        mock_action = object()
        with mock.patch('pgsqltoolsservice.disaster_recovery.disaster_recovery_service.Task', new=mock.Mock(return_value=mock_task)) as mock_task_constructor, \
                mock.patch('functools.partial', new=mock.Mock(return_value=mock_action)) as mock_partial:
            # When I call the backup request handler
            self.disaster_recovery_service.handle_backup_request(self.request_context, self.params)
            # Then a mock task is created and started
            mock_task_constructor.assert_called_once()
            mock_task.start.assert_called_once()
            # And the mock task was initialized with the expected parameters
            parameters = mock_task_constructor.call_args[0]
            self.assertEqual(parameters[2], constants.PROVIDER_NAME)
            self.assertEqual(parameters[3], self.host)
            self.assertEqual(parameters[4], self.dbname)
            self.assertIs(parameters[6], mock_action)
            mock_partial.assert_called_once_with(disaster_recovery_service._perform_backup, self.connection_info, self.params)
            # And the handler sends an empty response to indicate success
            self.assertEqual(self.request_context.last_response_params, {})

    def test_handle_backup_request_no_connection(self):
        """Test that the backup request handler responds with an error if there is no connection for the given owner URI"""
        # Set up a mock task so that the backup code does not actually run in a separate thread
        mock_task = mock.Mock()
        mock_action = object()
        with mock.patch('pgsqltoolsservice.disaster_recovery.disaster_recovery_service.Task', new=mock.Mock(return_value=mock_task)) as mock_task_constructor, \
                mock.patch('functools.partial', new=mock.Mock(return_value=mock_action)):
            # If I call the backup request handler and there is no connection corresponding to the given owner URI
            self.disaster_recovery_service.handle_backup_request(self.request_context, self.params)
            # Then a mock task is not created
            mock_task_constructor.assert_not_called()
            # And the handler sends an error response to indicate failure
            self.assertIsNotNone(self.request_context.last_error_message)
