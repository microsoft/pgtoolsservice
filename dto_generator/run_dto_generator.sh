# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#!/bin/bash

# Save the current directory and the script's directory, since DTO Generator must be run from the project root
pwd=$(pwd)
dirname=$(dirname "$0")

# Back up the old PYTHONPATH so it can be restored later
old_pythonpath=$PYTHONPATH

# Build the program
cd "$dirname/.."
export PYTHONPATH=$(pwd)
python dto_generator/dto_generator.py

# Restore the old PYTHONPATH and move back to the original directory
cd "$pwd"
export PYTHONPATH="$old_pythonpath"
