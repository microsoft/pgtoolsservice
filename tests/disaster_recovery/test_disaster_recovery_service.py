# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test the disaster recovery service"""

import os.path
import sys
from typing import Callable, List
import unittest
from unittest import mock

from pgsqltoolsservice.connection import ConnectionInfo, ConnectionService
from pgsqltoolsservice.connection.contracts import ConnectionDetails
from pgsqltoolsservice.disaster_recovery import disaster_recovery_service, DisasterRecoveryService
from pgsqltoolsservice.disaster_recovery.contracts import BackupParams, RestoreParams
from pgsqltoolsservice.tasks import Task, TaskService, TaskStatus
from pgsqltoolsservice.utils import constants
from tests import utils


class TestDisasterRecoveryService(unittest.TestCase):
    """Methods for testing the disaster recovery service"""

    def setUp(self):
        """Set up the tests with a disaster recovery service and connection service with mock connection info"""
        self.disaster_recovery_service = DisasterRecoveryService()
        self.connection_service = ConnectionService()
        self.task_service = TaskService()
        self.disaster_recovery_service._service_provider = utils.get_mock_service_provider({
            constants.CONNECTION_SERVICE_NAME: self.connection_service,
            constants.TASK_SERVICE_NAME: self.task_service})

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
        self.backup_path = 'mock/path/test.sql'
        self.backup_type = 'sql'
        self.data_only = False
        self.no_owner = True
        self.schema = 'test_schema'
        self.backup_params = BackupParams.from_dict({
            'ownerUri': self.test_uri,
            'backupInfo': {
                'type': self.backup_type,
                'path': self.backup_path,
                'data_only': self.data_only,
                'no_owner': self.no_owner,
                'schema': self.schema
            }
        })
        self.restore_path = 'mock/path/test.dump'
        self.restore_params = RestoreParams.from_dict({
            'ownerUri': self.test_uri,
            'options': {
                'path': self.restore_path,
                'data_only': self.data_only,
                'no_owner': self.no_owner,
                'schema': self.schema
            }
        })
        self.pg_dump_exe = 'pg_dump'
        self.pg_restore_exe = 'pg_restore'

        # Create the mock task for the tests
        self.mock_action = mock.Mock()
        self.mock_task = Task(None, None, None, None, None, self.request_context, self.mock_action)
        self.mock_task.start = mock.Mock()

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
                path = disaster_recovery_service._get_pg_exe_path(self.pg_dump_exe)
                # Then the path uses the mac directory and does not have a trailing .exe
                self.assertEqual(path, os.path.normpath('/pgsqltoolsservice/pgsqltoolsservice/pg_exes/mac/bin/pg_dump'))

                # If I get the executable path on Linux
                sys.platform = 'linux'
                path = disaster_recovery_service._get_pg_exe_path(self.pg_dump_exe)
                # Then the path uses the linux directory and does not have a trailing .exe
                self.assertEqual(path, os.path.normpath('/pgsqltoolsservice/pgsqltoolsservice/pg_exes/linux/bin/pg_dump'))

                # If I get the executable path on Windows
                sys.platform = 'win32'
                path = disaster_recovery_service._get_pg_exe_path(self.pg_dump_exe)
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
                path = disaster_recovery_service._get_pg_exe_path(self.pg_dump_exe)
                # Then the path uses the mac directory and does not have a trailing .exe
                self.assertEqual(path, os.path.normpath('/pgsqltoolsservice/build/pgtoolsservice/pg_exes/mac/bin/pg_dump'))

                # If I get the executable path on Linux
                sys.platform = 'linux'
                path = disaster_recovery_service._get_pg_exe_path(self.pg_dump_exe)
                # Then the path uses the linux directory and does not have a trailing .exe
                self.assertEqual(path, os.path.normpath('/pgsqltoolsservice/build/pgtoolsservice/pg_exes/linux/bin/pg_dump'))

                # If I get the executable path on Windows
                sys.platform = 'win32'
                path = disaster_recovery_service._get_pg_exe_path(self.pg_dump_exe)
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
        exe_name = self.pg_dump_exe
        test_method = disaster_recovery_service._perform_backup
        test_params = self.backup_params
        expected_args = [
            f'--file={self.backup_path}',
            '--format=p',
            f'--dbname={self.dbname}',
            f'--host={self.host}',
            f'--username={self.username}',
            '--no-owner',
            f'--schema={self.schema}'
        ]
        self._test_perform_backup_restore_internal(exe_name, test_method, test_params, expected_args)

    def test_perform_restore(self):
        """Test that the perform_restore method passes the correct parameters to pg_restore"""
        exe_name = self.pg_restore_exe
        test_method = disaster_recovery_service._perform_restore
        test_params = self.restore_params
        expected_args = [
            f'{self.restore_path}',
            f'--dbname={self.dbname}',
            f'--host={self.host}',
            f'--username={self.username}',
            '--no-owner',
            f'--schema={self.schema}'
        ]
        self._test_perform_backup_restore_internal(exe_name, test_method, test_params, expected_args)

    def _test_perform_backup_restore_internal(self, exe_name: str, test_method: Callable, test_params, expected_args: List[str]):
        mock_pg_path = f'mock/{exe_name}'
        mock_process = mock.Mock()
        mock_process.returncode = 0
        mock_process.communicate = mock.Mock(return_value=(b'', b''))
        with mock.patch('pgsqltoolsservice.disaster_recovery.disaster_recovery_service._get_pg_exe_path', new=mock.Mock(return_value=mock_pg_path)) \
                as mock_get_path, mock.patch('subprocess.Popen', new=mock.Mock(return_value=mock_process)) as mock_popen:
            # If I perform a backup/restore
            task_result = test_method(self.connection_info, test_params, self.mock_task)
            # Then the code got the path of the executable
            mock_get_path.assert_called_once_with(exe_name)
            # And ran the executable as a subprocess
            mock_popen.assert_called_once()
            # And then called communicate on the process
            mock_process.communicate.assert_called_once_with(b'')
            # And the arguments for the subprocess.Popen call were the expected values
            actual_args = mock_popen.call_args[0][0]
            self.assertEqual(actual_args[0], mock_pg_path)
            pg_exe_flags = actual_args[1:]
            for expected_arg in expected_args:
                self.assertIn(expected_arg, pg_exe_flags)
            self.assertEqual(len(expected_args), len(pg_exe_flags))
            # And the task returns a successful result
            self.assertIs(task_result.status, TaskStatus.SUCCEEDED)

    def test_perform_backup_fails(self):
        """Test that the perform_backup method handles failures by recording pg_dump's stderr output and marking the task failed"""
        self._test_perform_backup_restore_fails_internal(self.pg_dump_exe, disaster_recovery_service._perform_backup, self.backup_params)

    def test_perform_restore_fails(self):
        """Test that the perform_restore method handles failures by recording pg_dump's stderr output and marking the task failed"""
        self._test_perform_backup_restore_fails_internal(self.pg_restore_exe, disaster_recovery_service._perform_restore, self.restore_params)

    def _test_perform_backup_restore_fails_internal(self, exe_name: str, test_method: Callable, test_params):
        mock_pg_path = f'mock/{exe_name}'
        mock_process = mock.Mock()
        mock_process.returncode = 1
        test_error_message = b'test error message'
        mock_process.communicate = mock.Mock(return_value=(b'', test_error_message))
        with mock.patch('pgsqltoolsservice.disaster_recovery.disaster_recovery_service._get_pg_exe_path',
                        new=mock.Mock(return_value=mock_pg_path)), mock.patch('subprocess.Popen', new=mock.Mock(return_value=mock_process)):
            # If I perform a backup/restore that fails
            task_result = test_method(self.connection_info, test_params, self.mock_task)
            # Then the task returns a failed result
            self.assertIs(task_result.status, TaskStatus.FAILED)
            # And the task contains the error message from stderr
            self.assertEqual(task_result.error_message, str(test_error_message, 'utf-8'))

    def test_perform_backup_no_exe(self):
        """Test that the perform_backup task fails when the pg_dump exe is not found"""
        self._test_perform_backup_restore_no_exe_internal(disaster_recovery_service._perform_backup, self.backup_params)

    def test_perform_restore_no_exe(self):
        """Test that the perform_restore task fails when the pg_restore exe is not found"""
        self._test_perform_backup_restore_no_exe_internal(disaster_recovery_service._perform_restore, self.restore_params)

    def _test_perform_backup_restore_no_exe_internal(self, test_method: Callable, test_params):
        with mock.patch('os.path.exists', new=mock.Mock(return_value=False)), mock.patch('subprocess.Popen') as mock_popen:
            # If I perform a restore when the pg_restore executable cannot be found
            task_result = test_method(self.connection_info, test_params, mock.Mock())
            # Then the task fails and does try to kick off a new process
            self.assertIs(task_result.status, TaskStatus.FAILED)
            mock_popen.assert_not_called()

    def test_handle_backup_request(self):
        """Test that the backup request handler responds properly and kicks off a task to perform the backup"""
        self._test_handle_backup_restore_internal(self.disaster_recovery_service.handle_backup_request, disaster_recovery_service._perform_backup,
                                                  self.backup_params)

    def test_handle_restore_request(self):
        """Test that the restore request handler responds properly and kicks off a task to perform the restore"""
        self._test_handle_backup_restore_internal(self.disaster_recovery_service.handle_restore_request, disaster_recovery_service._perform_restore,
                                                  self.restore_params)

    def _test_handle_backup_restore_internal(self, test_handler: Callable, test_method: Callable, test_params):
        # Set up the connection service to return the test's connection information
        self.connection_service.owner_to_connection_map[self.test_uri] = self.connection_info
        # Set up a mock task so that the restore code does not actually run in a separate thread
        with mock.patch('pgsqltoolsservice.disaster_recovery.disaster_recovery_service.Task', new=mock.Mock(return_value=self.mock_task)) \
                as mock_task_constructor, mock.patch('functools.partial', new=mock.Mock(return_value=self.mock_action)) as mock_partial:
            # When I call the backup/restore request handler
            test_handler(self.request_context, test_params)
            # Then a mock task is created and started
            mock_task_constructor.assert_called_once()
            self.mock_task.start.assert_called_once()
            # And the mock task was initialized with the expected parameters
            parameters = mock_task_constructor.call_args[0]
            self.assertEqual(parameters[2], constants.PROVIDER_NAME)
            self.assertEqual(parameters[3], self.host)
            self.assertEqual(parameters[4], self.dbname)
            self.assertIs(parameters[6], self.mock_action)
            mock_partial.assert_called_once_with(test_method, self.connection_info, test_params)
            # And the handler sends an empty response to indicate success
            self.assertEqual(self.request_context.last_response_params, {})

    def test_handle_backup_request_no_connection(self):
        """Test that the backup request handler responds with an error if there is no connection for the given owner URI"""
        self._test_handle_backup_restore_request_no_connection(self.disaster_recovery_service.handle_backup_request, self.backup_params)

    def test_handle_restore_request_no_connection(self):
        """Test that the restore request handler responds with an error if there is no connection for the given owner URI"""
        self._test_handle_backup_restore_request_no_connection(self.disaster_recovery_service.handle_restore_request, self.restore_params)

    def _test_handle_backup_restore_request_no_connection(self, test_handler: Callable, test_params):
        # Set up a mock task so that the restore code does not actually run in a separate thread
        with mock.patch('pgsqltoolsservice.disaster_recovery.disaster_recovery_service.Task', new=mock.Mock(return_value=self.mock_task)) \
                as mock_task_constructor, mock.patch('functools.partial', new=mock.Mock(return_value=self.mock_action)):
            # If I call the request handler and there is no connection corresponding to the given owner URI
            test_handler(self.request_context, test_params)
            # Then a mock task is not created
            mock_task_constructor.assert_not_called()
            # And the handler sends an error response to indicate failure
            self.assertIsNotNone(self.request_context.last_error_message)

    def test_canceled_task_does_not_spawn_process(self):
        """Test that the pg_dump/pg_restore process is not created if the task has been canceled"""
        # Set up the task to be canceled
        self.mock_task.canceled = True

        with mock.patch('subprocess.Popen', new=mock.Mock()) as mock_popen:
            # If I try to perform a backup/restore for a canceled task
            disaster_recovery_service._perform_backup_restore(self.connection_info, [], {}, self.mock_task)

            # Then the process was not created
            mock_popen.assert_not_called()

    def test_cancel_backup(self):
        """Test that backups can be canceled by calling terminate on the pg_dump process"""
        # Set up the task to be canceled when communicate would normally be called

        def cancel_function(*_, **__):
            self.mock_task.cancel()
            return mock.DEFAULT

        self.mock_task.status = TaskStatus.IN_PROGRESS
        mock_process = mock.Mock()
        mock_process.communicate = mock.Mock(return_value=(None, None), side_effect=cancel_function)
        mock_process.terminate = mock.Mock()
        mock_process.returncode = 0
        with mock.patch('subprocess.Popen', new=mock.Mock(return_value=mock_process)):
            # If I perform a backup/restore that kicks off the subprocess and then I cancel the task
            disaster_recovery_service._perform_backup_restore(self.connection_info, [], {}, self.mock_task)

            # Then the backup/restore process was terminated
            mock_process.terminate.assert_called_once()
