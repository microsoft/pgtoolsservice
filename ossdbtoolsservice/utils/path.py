# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys

"""Utility functions for path handling"""

def get_application_base_path():
    """ Returns the base path of the application """
    # Construct the base path for the application
    base_path = os.path.dirname(os.path.abspath(sys.argv[0])) # In packaged mode, use the path relative to the binary's directory
    if not hasattr(sys, '_MEIPASS'):
        # In development mode, use the repository's root directory
        base_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), '..')
    return base_path

def path_relative_to_base(*paths):
    """ Returns the path of a file relative to the applications base or working directory """
    return os.path.join(get_application_base_path(), *paths)