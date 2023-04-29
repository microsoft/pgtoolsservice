# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import json
import sys

# Determine if the application is running as a packaged binary
is_packaged = getattr(sys, 'frozen', False)

root = os.path.dirname(__file__)

if is_packaged:
    # In packaged mode, use the path relative to the binary's directory
    literal_file = os.path.join(getattr(sys, '_MEIPASS', '.'), 'language', 'completion', 'packages', 'pgliterals', 'pgliterals.json')
else:
    # In development mode, use the path relative to this file's directory
    literal_file = os.path.join(root, 'pgliterals.json')

# Check if the path points to a directory
if os.path.isdir(literal_file):
    print(f"Path '{literal_file}' points to a directory, which is unexpected.")
    sys.exit(1)

with open(literal_file) as f:
    literals = json.load(f)


def get_literals(literal_type, type_=tuple):
    # Where `literal_type` is one of 'keywords', 'functions', 'datatypes',
    # returns a tuple of literal values of that type.

    return type_(literals[literal_type])
