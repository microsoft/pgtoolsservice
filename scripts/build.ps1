# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Save the current directory and the script's directory, since build must be run from the project root
$curloc = $pwd
$scriptloc = $PSScriptRoot

# Back up the old PYTHONPATH so it can be restored later
$oldPythonpath=$Env:PYTHONPATH

# Build the program
Set-Location $scriptloc/..
$Env:PYTHONPATH = ""
pip3 install -r requirements.txt
pyinstaller ossdbtoolsservice_main.spec

# create folder pgsqltoolsservice in dist folder
New-Item -ItemType Directory -Force -Path ".\dist\pgsqltoolsservice"

# Move the contents in the dist folder to pgsqltoolsservice folder
Get-ChildItem -Path ".\dist" | Where-Object { !$_.PSIsContainer } | Move-Item -Destination ".\dist\pgsqltoolsservice"

# copy pg_exe folder to pgsqltoolsservice
Copy-Item ".\ossdbtoolsservice\pg_exes" ".\dist\pgsqltoolsservice\pg_exes" -Recurse

# Restore the old PYTHONPATH and move back to the original directory
Set-Location $curloc
$Env:PYTHONPATH = $oldPythonpath
