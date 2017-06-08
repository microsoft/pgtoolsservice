# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from typing import List, Optional               # noqa
from urllib.parse import urlparse, ParseResult  # noqa
from threading import Lock

from pgsqltoolsservice.workspace.script_file import ScriptFile
import pgsqltoolsservice.utils as utils


class Workspace:
    """
    Manages a "workspace" of script files that are open for a particular editing session. Also helps to navigate
    references between script files.
    """

    def __init__(self):
        self._workspace_files: dict = {}
        self._workspace_files_lock: Lock = Lock()

    # PROPERTIES ###########################################################
    @property
    def opened_files(self) -> List[ScriptFile]:
        """
        A list of all ScriptFiles that are currently open
        """
        return list(self._workspace_files.values())

    # METHODS ##############################################################
    def close_file(self, file_path: str) -> [ScriptFile, None]:
        """
        Closes a currently open script fil
        :param file_path: The file to close
        :return: The ScriptFile that was closed, or None if the file is not open
        """
        utils.validate.is_not_none_or_whitespace("file_path", file_path)

        # Resolve the full file path
        resolved_file_path: str = self._resolve_file_path(file_path)
        key_name: str = resolved_file_path.lower()

        with self._workspace_files_lock:
            # Get the requested file, and delete it if it exists
            # Note: This is performed inside a lock context b/c we need this operation to be atomic
            requested_file: ScriptFile = self._workspace_files.get(key_name)
            if requested_file is not None:
                del self._workspace_files[key_name]
            return requested_file

    def contains_file(self, file_path: str) -> bool:
        """
        Checks if a given URI is contained in a workspace
        :param file_path: Path to the file to check whether or not it is open
        :return: Flag indicating if the file is tracked in workspace
        """
        utils.validate.is_not_none_or_whitespace(u"file_path", file_path)

        # Resolve the full file path
        resolved_file_path: str = self._resolve_file_path(file_path)
        key_name: str = resolved_file_path.lower()

        return key_name in self._workspace_files

    def open_file(self, file_path: str, initial_buffer: Optional[str]=None) -> [ScriptFile, None]:
        """
        Opens a file in the workspace
        :param file_path: Path to the file to load
        :param initial_buffer: Optionally the initial contents of the file
        :return: ScriptFile representing the file that was opened
        """
        utils.validate.is_not_none_or_whitespace("file_path", file_path)

        # Validate that the path is not an SCM path
        if self._is_scm_path(file_path):
            return None

        # Resolve the full file path
        # TODO: Validate that this works with operating systems that allow files to differ by case only (ie, linux)
        resolved_file_path: str = self._resolve_file_path(file_path)
        key_name: str = resolved_file_path.lower()

        # If the file is already loaded in the workspace, just return it
        script_file: ScriptFile = self._workspace_files.get(key_name)
        if script_file is not None:
            return script_file

        # The script file isn't already loaded into the workspace. Open it.
        if initial_buffer is None:
            # An initial buffer wasn't provided, load the contents
            with open(resolved_file_path, 'r') as file:
                initial_buffer = file.read()
        script_file = ScriptFile(resolved_file_path, file_path, initial_buffer)
        return script_file

    def get_file(self, file_path: str) -> [ScriptFile, None]:
        """
        Gets an open file in the workspace. If the file isn't open, return None
        :param file_path: File path at which the file to load exists
        :return: ScriptFile representing the file that was loaded, None if the file isn't open
        """
        utils.validate.is_not_none_or_whitespace("file_path", file_path)

        # Resolve the full file path
        resolved_file_path: str = self._resolve_file_path(file_path)
        key_name: str = resolved_file_path.lower()

        # Make sure the file isn't already loaded into the workspace
        script_file: ScriptFile = self._workspace_files.get(key_name)

        return script_file

    # IMPLEMENTATION DETAILS ###############################################
    @staticmethod
    def _is_path_in_memory(file_path: str) -> bool:
        """
        Determines if a file path is an "in-memory" path based on the schema it starts with
        :param file_path: Path to determine if it is in-memory
        :return: True if the path is in-memory, false otherwise
        """
        return file_path.startswith('inmemory:')\
            or file_path.startswith('tsqloutput:')\
            or file_path.startswith('git:')\
            or file_path.startswith('untitled:')

    @staticmethod
    def _is_scm_path(file_uri: str):
        """
        If the URI is prefixed with git: then we want to skip processing the file
        :param file_uri: URI for the file to check
        """
        return file_uri.startswith('git:')

    def _resolve_file_path(self, file_path: str):
        if not self._is_path_in_memory(file_path):
            if file_path.startswith('file://'):
                # Client sent the path in URI format, extract the local path and trim any extraneous slashes
                file_uri: ParseResult = urlparse(file_path)
                file_path: str = file_uri.path.lstrip('/')

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
