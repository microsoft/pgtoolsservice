# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Save the current directory and the script's directory, since DTO Generator must be run from the project root.
$curloc = $pwd
$scriptloc = $PSScriptRoot

# Back up the old PYTHONPATH so it can be restored later
$oldPythonpath=$Env:PYTHONPATH

# Build the program
Set-Location $scriptloc/..
$Env:PYTHONPATH = (Get-Location).Path
python dto_generator/dto_generator.py

# Restore the old PYTHONPATH and move back to the original directory
Set-Location $curloc
$Env:PYTHONPATH = $oldPythonpath
