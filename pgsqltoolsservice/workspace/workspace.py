# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from typing import List
from urllib.parse import urlparse, ParseResult

from utils import validate
from workspace.script_file import ScriptFile


class Workspace:
    """
    Manages a "workspace" of script files that are open for a particular editing session. Also helps to navigate
    references between script files.
    
    Attributes:
        workspace_path  
    """

    def __init__(self):
        self._workspace_files: dict = {}

    # PROPERTIES ###########################################################
    @property
    def opened_files(self) -> List[ScriptFile]:
        """
        A list of all ScriptFiles that are currently open
        """
        return list(self._workspace_files.values())

    # METHODS ##############################################################
    def close_file(self, file_path: str) -> None:
        """
        Closes a currently open script fil
        :param file_path: The file to close
        """
        validate.is_not_none_or_whitespace("file_path", file_path)

        del self._workspace_files[file_path]

    def contains_file(self, file_path: str) -> bool:
        """
        Checks if a given URI is contained in a workspace
        :param file_path: Path to the file to check whether or not it is open
        :return: Flag indicating if the file is tracked in workspace
        """
        validate.is_not_none_or_whitespace(u"file_path", file_path)

        # Resolve the full file path
        resolved_file_path: str = self._resolve_file_path(file_path)
        key_name: str = resolved_file_path.lower()

        return key_name in self._workspace_files

    def get_file(self, file_path: str) -> ScriptFile:
        """
        Gets an open file in the workspace. If the file isn't open but exists on the filesystem, load and return it
        :param file_path: File path at which the file to load exists
        :return: ScriptFile representing the file that was loaded
        """
        validate.is_not_none_or_whitespace("file_path", file_path)

        # Resolve the full file path
        # TODO: Validate that this works with operating systems that allow files to differ by case only (ie, linux)
        resolved_file_path: str = self._resolve_file_path(file_path)
        key_name: str = resolved_file_path.lower()

        # Make sure the file isn't already loaded into the workspace
        script_file: ScriptFile = self._workspace_files.get(key_name)
        if script_file is None:
            # Open the file and read it all at once
            with open(resolved_file_path, 'r') as file:
                content = file.read()
                script_file = ScriptFile(resolved_file_path, content)
                self._workspace_files[key_name] = script_file
            #TODO: Log
        # TODO: Shouldn't this return None if the file isn't open? Seems pointless to open the files in two places

        return script_file

    def get_file_buffer(self, file_path: str, initial_buffer) -> ScriptFile:
        """
        Gets a new ScriptFile instance identified by the given file path and initially contains the given buffer
        :param file_path: Path of the file to create a script file for
        :param initial_buffer: Initial contents of the script file
        :return: ScriptFile that represents the file that was opened
        """
        validate.is_not_none_or_whitespace("file_path", file_path)

        # Resolve the full file path
        resolved_file_path = self._resolve_file_path(file_path)
        key_name = resolved_file_path.lower()

        # Make sure the file isn't already loaded into the workspace
        script_file: ScriptFile = self._workspace_files.get(key_name)
        if script_file is None:
            script_file = ScriptFile(resolved_file_path, file_path, initial_buffer)
            self._workspace_files[key_name] = script_file
            # TODO: Log.

        return script_file

    # IMPLEMENTATION DETAILS ###############################################
    @staticmethod
    def _is_path_in_memory(file_path: str) -> bool:
        """
        Determines if a file path is an "in-memory" path based on the schema it starts with
        :param file_path: Path to determine if it is in-memory
        :return: True if the path is in-memory, false otherwise
        """
        return file_path.startswith(u"inmemory:")\
            or file_path.startswith(u"tsqloutput:")\
            or file_path.startswith(u"git:")\
            or file_path.startswith(u"untitled:")

    def _resolve_file_path(self, file_path: str):
        if not self._is_path_in_memory(file_path):
            if file_path.startswith(u"file://"):
                # Client sent the path in URI format, extract the local path and trim any extraneous slashes
                file_uri: ParseResult = urlparse(file_path)
                file_path = file_uri.path.lstrip('/')

            # Some clients send paths with UNIX-style slashes, replace those if necessary
            # TODO: Validate that this works properly
            file_path = file_path.replace('/', '\\')

            # Get the absolute file path
            file_path = os.path.abspath(file_path)

        return file_path

    @staticmethod
    def _resolve_relative_script_path(base_file_path: str, relative_path: str) -> str:
        # Skip resolution if the path is already absolute
        if os.path.isabs(relative_path):
            return relative_path

        # Get the directory of the original script file, combine it with the given path and then resolve the absolute
        # file path
        return os.path.abspath(os.path.join(base_file_path, relative_path))
