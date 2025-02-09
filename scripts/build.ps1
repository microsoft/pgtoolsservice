# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Pass in "webserver" if building the webserver version of the service
param (
    [string]$ARG
)

# Save the current directory and the script's directory, since build must be run from the project root
$curloc = $pwd
$scriptloc = $PSScriptRoot

# Back up the old PYTHONPATH so it can be restored later
$oldPythonpath=$Env:PYTHONPATH

# Build the program
Set-Location $scriptloc/..
$Env:PYTHONPATH = ""

pip3 install -e .[dev]
pyinstaller ossdbtoolsservice_main.spec

# create folder pgsqltoolsservice in dist folder
New-Item -ItemType Directory -Force -Path ".\dist\pgsqltoolsservice"

# Move the contents in the dist folder to pgsqltoolsservice folder
Get-ChildItem -Path ".\dist" | Where-Object { !$_.PSIsContainer } | Move-Item -Destination ".\dist\pgsqltoolsservice"

# Only copy the development SSL certificate and config file if "webserver" argument is passed
if ($ARG -eq "webserver") {
    # Copy the development SSL certificate to the pgsqltoolsservice folder
    New-Item -ItemType Directory -Force -Path ".\dist\pgsqltoolsservice\ssl"
    Copy-Item ".\ssl\cert.pem" ".\dist\pgsqltoolsservice\ssl\cert.pem"
    Copy-Item ".\ssl\key.pem" ".\dist\pgsqltoolsservice\ssl\key.pem"

    # Copy the pgsqltoolsservice config file to the dist folder
    Copy-Item ".\config.ini" ".\dist\pgsqltoolsservice\config.ini"
}

# copy pg_exe folder to pgsqltoolsservice
Copy-Item ".\ossdbtoolsservice\pg_exes\win" ".\dist\pgsqltoolsservice\pg_exes\win" -Recurse

# Restore the old PYTHONPATH and move back to the original directory
Set-Location $curloc
$Env:PYTHONPATH = $oldPythonpath
