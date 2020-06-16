# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Tuple, Optional
import unittest
import unittest.mock as mock

from ostoolsservice.workspace.workspace import ScriptFile, Workspace


class TestWorkspaceService(unittest.TestCase):
    def test_init(self):
        # If: I create a workspace
        w: Workspace = Workspace()

        # Then:
        # ... The list of files should be initialized to empty
        self.assertDictEqual(w._workspace_files, {})
        self.assertListEqual(w.opened_files, [])

    def test_file_operations_no_path(self):
        # Setup: Create list of paths to try and a list of methods to run
        w: Workspace = Workspace()
        test_methods = [w.close_file, w.contains_file, w.open_file, w.get_file]
        test_paths = [None, '', '  \t\t\r\n\r\n']

        for method in test_methods:
            for path in test_paths:
                with self.assertRaises(ValueError):
                    # If: The workspace is asked to perform a file operation with a missing file path
                    # Then: It should raise an exception
                    method(path)

    # CONTAINS_FILE TESTS ##################################################

    def test_contains_file_true(self):
        # If: The workspace is asked if it contains a file that is opened
        w, sf = self._get_test_workspace()
        result = w.contains_file(sf.file_uri)

        # Then: The result should be true
        self.assertTrue(result)

    def test_contains_file_false(self):
        # If: The workspace is asked if it contains a file that is not opened
        w, sf = self._get_test_workspace()
        result = w.contains_file('nonexistent')

        # Then: The result should be false
        self.assertFalse(result)

    # OPEN_FILE TESTS ######################################################

    def test_open_file_scm(self):
        # If: I open a file that is a SCM file
        w, sf = self._get_test_workspace()
        result = w.open_file('git://scm-path')

        # Then: The result should be None
        self.assertIsNone(result)

    def test_open_file_opened(self):
        # If: I open a file that is already open
        w, sf = self._get_test_workspace()
        result = w.open_file(sf.file_uri)

        # Then: The "opened" file should be the already open one
        self.assertIs(result, sf)

    def test_open_file_no_buffer(self):
        # Setup: Patch open()
        m = mock.mock_open()
        with mock.patch('ostoolsservice.workspace.workspace.open', m, create=True):
            # If: I open a file without a buffer
            w, sf = self._get_test_workspace(False)
            result = w.open_file("file_path", None)

            # Then:
            # ... A file should have been opened
            m.assert_called_once_with("file_path", 'r')

            # ... Opening the file should have been successful
            self.assertIsInstance(result, ScriptFile)
            self.assertDictEqual(w._workspace_files, {result.file_uri: result})
            self.assertListEqual(w.opened_files, [result])

    def test_open_file_no_buffer_no_file(self):
        with self.assertRaises(ValueError):
            # If: I open a file without a buffer and with an "in-memory" uri
            w, sf = self._get_test_workspace(False)
            w.open_file("untitled://stuff", None)
            # Then: I should get an exception

    def test_open_file_with_buffer(self):
        # If: I open a file with a buffer
        w, sf = self._get_test_workspace(False)
        result = w.open_file("untitled://stuff", "sample buffer")

        # Then:
        # ... A script file should have been created
        self.assertIsInstance(result, ScriptFile)
        self.assertDictEqual(w._workspace_files, {result.file_uri: result})
        self.assertListEqual(w.opened_files, [result])

    # GET_FILE TESTS #######################################################

    def test_get_file_open(self):
        # If: I attempt to retrieve a file that is already open
        w, sf = self._get_test_workspace()
        result = w.get_file(sf.file_uri)

        # Then: I should have gotten the file back
        self.assertIs(result, sf)

    def test_get_file_not_open(self):
        # If: I attempt to retrieve a file that is not open
        w, sf = self._get_test_workspace()
        result = w.get_file('not_opened')

        # Then: I should have gotten None back
        self.assertIsNone(result)

    # CLOSE_FILE TESTS #####################################################

    def test_close_file_open(self):
        # If: I attempt to close a file that is already open
        w, sf = self._get_test_workspace()
        result = w.close_file(sf.file_uri)

        # Then:
        # ... I should have gotten the closed file back
        self.assertIs(result, sf)

        # ... The file should no longer be in the workspace files
        self.assertDictEqual(w._workspace_files, {})
        self.assertListEqual(w.opened_files, [])

    def test_close_file_not_open(self):
        # If: I attempt to close a file that is not open
        w, sf = self._get_test_workspace(False)
        result = w.close_file('file_path')

        # Then:
        # ... I should get none back
        self.assertIsNone(result)

    # _IS_PATH_IN_MEMORY TESTS #############################################

    def test_is_path_in_memory(self):
        # Setup: Define the tests to run
        tests = [
            ('file://path', False),                 # Non-memory path
            ('file://inmemory:/path', False),       # inmemory in middle of path
            ('file://tsqloutput:/path', False),     # tsqloutput in middle of path
            ('file://git:/path', False),            # git in middle of path
            ('file://untitled:/path', False),       # untitled in middle of path
            ('inmemory://path', True),              # Starts with inmemory
            ('tsqloutput://path', True),            # Starts with tsqloutput
            ('git://path', True),                   # Starts with git
            ('untitled://path', True)               # Starts with untitled
        ]

        for test in tests:
            # If: I check to see if a path is in memory
            result = Workspace._is_path_in_memory(test[0])

            # Then: I should get the result as from the test definition
            self.assertEqual(result, test[1])

    # _IS_SCM_PATH TESTS ###################################################

    def test_is_path_scm(self):
        # Setup: Define the tests to run
        tests = [
            ('file://path', False),  # Non-memory path
            ('file://git:/path', False),  # git in middle of path
            ('git://path', True),  # Starts with git
        ]

        for test in tests:
            # If: I check to see if a path is in memory
            result = Workspace._is_path_in_memory(test[0])

            # Then: I should get the result as from the test definition
            self.assertEqual(result, test[1])

    # _RESOLVE_FILE_PATH TESTS #############################################

    def test_resolve_file_path_windows(self):
        # Setup: Define tests to run
        tests = [
            ('untitled://filename', None),          # URI is in memory, exercises early back-out
            ('/path/to/file', '/path/to/file'),     # URI was not actually a URI, skips URI parsing
            ('file://server/path/to/file', '\\\\server\\path\\to\\file'),
            ('file:///D%3A/path/to/file', 'D:\\path\\to\\file'),
        ]

        with mock.patch('ostoolsservice.workspace.workspace.os.name', 'nt'):
            for test in tests:
                # If: I attempt to resolve a URI to a file path in windows (aka 'nt'
                result = Workspace._resolve_file_path(test[0])

                # Then: I should get the expected output
                self.assertEqual(result, test[1])

    def test_resolve_file_path_posix(self):
        # Setup: Define tests to run
        tests = [
            ('untitled://filename', None),  # URI is in memory, exercises early back-out
            ('/path/to/file', '/path/to/file'),  # URI was not actually a URI, skips URI parsing
            ('file://server/path/to/file', '//server/path/to/file'),
            ('file:///path%20space/to/file', '/path space/to/file'),
        ]

        with mock.patch('ostoolsservice.workspace.workspace.os.name', 'posix'):
            for test in tests:
                # If: I attempt to resolve a URI to a file path in OSX/Linux (aka 'posix')
                result = Workspace._resolve_file_path(test[0])

                # Then: I should get the expected output
                self.assertEqual(result, test[1])

    # IMPLEMENTATION DETAILS ###############################################

    @staticmethod
    def _get_test_workspace(script_file: bool = True) -> Tuple[Workspace, Optional[ScriptFile]]:
        w: Workspace = Workspace()
        sf: Optional[ScriptFile] = None
        if script_file:
            sf = ScriptFile('file_path', 'client_path', '')
            w._workspace_files['file_path'] = sf

        return w, sf
