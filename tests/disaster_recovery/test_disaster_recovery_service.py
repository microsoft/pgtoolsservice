# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test the disaster recovery service"""

import sys
import unittest
from unittest import mock

from pgsqltoolsservice.connection import ConnectionInfo, ConnectionService
from pgsqltoolsservice.connection.contracts import ConnectionDetails
from pgsqltoolsservice.disaster_recovery import disaster_recovery_service
from pgsqltoolsservice.disaster_recovery import DisasterRecoveryService
from pgsqltoolsservice.disaster_recovery.contracts.backup import BackupParams, DefaultDatabaseInfoParams
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

    def test_get_pg_exe_path_local(self):
        """Test the get_pg_exe_path function when the service is running from source code"""
        # Back up these values so that the test can overwrite them
        old_arg0 = sys.argv[0]
        old_platform = sys.platform
        try:
            # Override sys.argv[0] to simulate running the code directly from source
            sys.argv[0] = '/Users/mairvine/code/pgsqltoolsservice/pgsqltoolsservice/pgtoolsservice_main.py'

            # If I get the executable path on Mac
            sys.platform = 'darwin'
            path = disaster_recovery_service._get_pg_exe_path('pg_dump')
            # Then the path uses the mac directory and does not have a trailing .exe
            self.assertEqual(path, '/Users/mairvine/code/pgsqltoolsservice/pgsqltoolsservice/pg_exes/mac/bin/pg_dump')

            # If I get the executable path on Linux
            sys.platform = 'linux'
            path = disaster_recovery_service._get_pg_exe_path('pg_dump')
            # Then the path uses the linux directory and does not have a trailing .exe
            self.assertEqual(path, '/Users/mairvine/code/pgsqltoolsservice/pgsqltoolsservice/pg_exes/linux/bin/pg_dump')

            # If I get the executable path on Windows
            sys.platform = 'win32'
            path = disaster_recovery_service._get_pg_exe_path('pg_dump')
            # Then the path uses the win directory and does have a trailing .exe
            self.assertEqual(path, '/Users/mairvine/code/pgsqltoolsservice/pgsqltoolsservice/pg_exes/win/bin/pg_dump.exe')
        finally:
            sys.argv[0] = old_arg0
            sys.platform = old_platform

    def test_get_pg_exe_path_frozen(self):
        """Test the get_pg_exe_path function when the service is running from a cx_freeze build"""
        # Back up these values so that the test can overwrite them
        old_arg0 = sys.argv[0]
        old_platform = sys.platform
        try:
            # Override sys.argv[0] to simulate running the code from a cx_freeze build
            sys.argv[0] = '/Users/mairvine/code/pgsqltoolsservice/build/pgtoolsservice/pgtoolsservice_main'

            # If I get the executable path on Mac
            sys.platform = 'darwin'
            path = disaster_recovery_service._get_pg_exe_path('pg_dump')
            # Then the path uses the mac directory and does not have a trailing .exe
            self.assertEqual(path, '/Users/mairvine/code/pgsqltoolsservice/build/pgtoolsservice/pg_exes/mac/bin/pg_dump')

            # If I get the executable path on Linux
            sys.platform = 'linux'
            path = disaster_recovery_service._get_pg_exe_path('pg_dump')
            # Then the path uses the linux directory and does not have a trailing .exe
            self.assertEqual(path, '/Users/mairvine/code/pgsqltoolsservice/build/pgtoolsservice/pg_exes/linux/bin/pg_dump')

            # If I get the executable path on Windows
            sys.platform = 'win32'
            path = disaster_recovery_service._get_pg_exe_path('pg_dump')
            # Then the path uses the win directory and does have a trailing .exe
            self.assertEqual(path, '/Users/mairvine/code/pgsqltoolsservice/build/pgtoolsservice/pg_exes/win/bin/pg_dump.exe')
        finally:
            sys.argv[0] = old_arg0
            sys.platform = old_platform

    def test_handle_backup_config_info_request(self):
        """Test that handle_backup_config_info_request sends back a hardcoded response"""
        # Set up the parameters for the test
        request_context = utils.MockRequestContext()
        params = DefaultDatabaseInfoParams()

        # If I call handle_backup_config_info_request
        disaster_recovery_service.handle_backup_config_info_request(request_context, params)

        # Then a hardcoded response was sent
        self.assertEqual(
            request_context.last_response_params,
            {'backupConfigInfo': {'lastBackupLocations': [], 'defaultNewBackupFolder': '', 'recoveryModel': 'Simple', 'backupEncryptors': []}})

    def test_perform_backup(self):
        """Test that the perform_backup method passes the correct parameters to pg_dump"""
        # Set up the parameters and mocks for the test
        backup_path = 'test_path'
        params = BackupParams.from_dict({
            'ownerUri': self.test_uri,
            'backupInfo': {
                'ownerUri': self.test_uri,
                'databaseName': self.dbname,
                'backup_path_list': [backup_path]
            }
        })
        mock_pg_path = 'mock/pg_dump'
        mock_process = mock.Mock()
        with mock.patch('pgsqltoolsservice.disaster_recovery.disaster_recovery_service._get_pg_exe_path',
                        new=mock.Mock(return_value=mock_pg_path)) as mock_get_path, \
                mock.patch('subprocess.Popen', new=mock.Mock(return_value=mock_process)) as mock_popen:
            # If I perform a backup
            disaster_recovery_service.perform_backup(self.connection_info, params)
            # Then the code got the path of pg_dump
            mock_get_path.assert_called_once_with('pg_dump')
            # And ran the pg_dump executable as a subprocess
            mock_popen.assert_called_once()
            # And then called communicate on the process
            mock_process.communicate.assert_called_once_with(b'')
            # And the arguments for the subprocess.Popen call were the expected values
            expected_args = [
                f'--file={backup_path}',
                '--format=p',
                f'--dbname={self.dbname}',
                f'--host={self.host}',
                f'--username={self.username}'
            ]
            actual_args = mock_popen.call_args[0][0]
            self.assertEqual(actual_args[0], mock_pg_path)
            for expected_arg in expected_args:
                self.assertIn(expected_arg, actual_args)

    def test_handle_backup_request(self):
        """Test that the backup request handler responds properly and kicks off a task to perform the backup"""
        # Set up the parameters for the test
        request_context = utils.MockRequestContext()
        backup_path = 'mock/pg_dump'
        params = BackupParams.from_dict({
            'ownerUri': self.test_uri,
            'backupInfo': {
                'ownerUri': self.test_uri,
                'databaseName': self.dbname,
                'backup_path_list': [backup_path]
            }
        })
        # Set up the connection service to return the test's connection information
        self.connection_service.owner_to_connection_map[self.test_uri] = self.connection_info
        # Set up a mock task so that the backup code does not actually run in a separate thread
        mock_task = mock.Mock()
        mock_action = object()
        with mock.patch('pgsqltoolsservice.disaster_recovery.disaster_recovery_service.Task', new=mock.Mock(return_value=mock_task)) as mock_task_constructor, \
                mock.patch('functools.partial', new=mock.Mock(return_value=mock_action)) as mock_partial:
            # When I call the backup request handler
            self.disaster_recovery_service.handle_backup_request(request_context, params)
            # Then a mock task is created and started
            mock_task_constructor.assert_called_once()
            mock_task.start.assert_called_once()
            # And the mock task was initialized with the expected parameters
            parameters = mock_task_constructor.call_args[0]
            self.assertEqual(parameters[2], constants.PROVIDER_NAME)
            self.assertEqual(parameters[3], self.host)
            self.assertEqual(parameters[4], self.dbname)
            self.assertIs(parameters[6], mock_action)
            mock_partial.assert_called_once_with(disaster_recovery_service.perform_backup, self.connection_info, params)
            # And the handler sends an empty response to indicate success
            self.assertEqual(request_context.last_response_params, {})
