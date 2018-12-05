# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from typing import List, Optional                        # noqa
from urllib.parse import urlparse, unquote, ParseResult  # noqa

from pgsqltoolsservice.workspace.script_file import ScriptFile
import pgsqltoolsservice.utils as utils


class Workspace:
    """
    Manages a "workspace" of script files that are open for a particular editing session. Also helps to navigate
    references between script files.
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
    def close_file(self, file_uri: str) -> Optional[ScriptFile]:
        """
        Closes a currently open script file
        :param file_uri: URI to identify the script file as provided by the client
        :return: The ScriptFile that was closed, or None if the file is not open
        """
        utils.validate.is_not_none_or_whitespace("file_uri", file_uri)

        return self._workspace_files.pop(file_uri, None)

    def contains_file(self, file_uri: str) -> bool:
        """
        Checks if a given URI is contained in a workspace
        :param file_uri: URI for the file, as provided by the client
        :return: Flag indicating if the file is tracked in workspace
        """
        utils.validate.is_not_none_or_whitespace('file_uri', file_uri)

        return file_uri in self._workspace_files

    def open_file(self, file_uri: str, initial_buffer: Optional[str] = None) -> Optional[ScriptFile]:
        """
        Opens a file in the workspace
        :param file_uri: URI to identify the script file, provided by the client
        :param initial_buffer: Optionally the initial contents of the file
        :return: ScriptFile representing the file that was opened
        """
        utils.validate.is_not_none_or_whitespace("file_uri", file_uri)

        # Validate that the path is not an SCM path
        if self._is_scm_path(file_uri):
            return None

        # Resolve the full file path
        resolved_file_path: str = self._resolve_file_path(file_uri)

        # If the file is already loaded in the workspace, just return it
        script_file: ScriptFile = self._workspace_files.get(file_uri)
        if script_file is not None:
            return script_file

        # The script file isn't already loaded into the workspace. Open it.
        if initial_buffer is None:
            if resolved_file_path is None:
                # We can't create a script file if we don't have a buffer
                # TODO: Localize
                raise ValueError(f'File uri {file_uri} could not be resolved and file contents not provided.')

            # An initial buffer wasn't provided, load the contents
            with open(resolved_file_path, 'r') as file:
                initial_buffer = file.read()
        script_file = ScriptFile(file_uri, initial_buffer, resolved_file_path)
        self._workspace_files[file_uri] = script_file
        return script_file

    def get_file(self, file_uri: str) -> [ScriptFile, None]:
        """
        Gets an open file in the workspace. If the file isn't open, return None
        :param file_uri: URI to identify the file, provided by the client
        :return: ScriptFile representing the file that was loaded, None if the file isn't open
        """
        utils.validate.is_not_none_or_whitespace("file_uri", file_uri)

        return self._workspace_files.get(file_uri)

    # IMPLEMENTATION DETAILS ###############################################
    @staticmethod
    def _is_path_in_memory(file_uri: str) -> bool:
        """
        Determines if a file path is an "in-memory" path based on the schema it starts with
        :param file_uri: URI for the script file
        :return: True if the path is in-memory, false otherwise
        """
        return file_uri.startswith('inmemory:') \
            or file_uri.startswith('tsqloutput:') \
            or file_uri.startswith('git:') \
            or file_uri.startswith('untitled:')

    @staticmethod
    def _is_scm_path(file_uri: str):
        """
        If the URI is prefixed with git: then we want to skip processing the file
        :param file_uri: URI for the file to check
        """
        return file_uri.startswith('git:')

    @staticmethod
    def _resolve_file_path(file_uri: str) -> Optional[str]:
        """
        Resolves the file URI into a path on disk based on the protocol of the uri
        :param file_uri: URI provided by the client to identify the file
        :return: None if the file is in memory, the location of the file if it is on disk
        """
        if Workspace._is_path_in_memory(file_uri):
            # File is not on disk
            return None

        # File is on disk. Resolve where it could be.
        file_path: str = file_uri
        if file_path.startswith('file://'):
            # This *should* always be the case, but it might not be if the client isn't adhering to
            # the protocol properly
            # Client sent a URI format path. Extract the path and possibly the host name
            uri: ParseResult = urlparse(file_path)

            if os.name == 'nt':
                # If we're on windows, we need to do special processing
                if uri.netloc != '':
                    # eg: file://server/path/to/file -> //server/path/to/file
                    # Path is to a remote machine
                    file_path = f'//{unquote(uri.netloc)}{unquote(uri.path)}'
                else:
                    # eg: file:///d%3A/path/to/file -> d:/path/to/file
                    # Path is local, and starts with an invalid /
                    file_path = unquote(uri.path[1:])

                # Convert / to \
                # eg: d:/path/to/file -> d:\path\to\file
                file_path = file_path.replace('/', '\\')
            else:
                if uri.netloc != '':
                    # eg: file://server/path/to/file -> //server/path/to/file
                    # Path is to a remote machine. Very uncommon to have a UNC path on OSX/Linux
                    file_path = f'//{unquote(uri.netloc)}{unquote(uri.path)}'
                else:
                    # eg: file:///path/to/file -> /path/to/file
                    file_path = unquote(uri.path)

        # If the URI doesn't start with file:// then it is likely an absolute path to the file
        return file_path
