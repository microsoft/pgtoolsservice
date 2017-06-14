# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module for testing the workspace service"""

import unittest

from pgsqltoolsservice.query_execution.contracts import SelectionData
from pgsqltoolsservice.workspace import WorkspaceService


class WorkspaceServiceTests(unittest.TestCase):
    """Class for testing the workspace service"""

    def test_get_text_full(self):
        """Text the workspace service's public get_text method when getting the full text of a file"""
        # Set up the service with a file
        workspace_service = WorkspaceService()
        file_uri = 'untitled:Test_file'
        file_text = 'line1\nline 2 content\n line 3 '
        workspace_service._workspace.open_file(file_uri, file_text)

        # Retrieve the full text of the file and make sure it matches
        result_text = workspace_service.get_text(file_uri, None)
        self.assertEqual(result_text, file_text)

    def test_get_text_selection(self):
        """Text the workspace service's public get_text method when getting a selection of the text of a file"""
        # Set up the service with a file
        workspace_service = WorkspaceService()
        file_uri = 'untitled:Test_file'
        file_text = 'line1\nline 2 content\n line 3 '
        workspace_service._workspace.open_file(file_uri, file_text)

        # Retrieve the full text of the file and make sure it matches
        selection_data = SelectionData()
        selection_data.start_line = 1
        selection_data.start_column = 1
        selection_data.end_line = 2
        selection_data.end_column = 4
        result_text = workspace_service.get_text(file_uri, selection_data)
        self.assertEqual(result_text, 'ine 2 content\n line')
