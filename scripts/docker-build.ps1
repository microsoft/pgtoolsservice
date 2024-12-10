# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

param (
    [string]$BuildVersion
)

if (-not $BuildVersion) {
    $BuildVersion = (Get-Date -Format "yyyy-MM-dd-HH-mm-ss")
}

write-host "BuildVersion: $BuildVersion"

# Save the current directory and the script's directory, since build must be run from the project root
$curloc = $pwd
$scriptloc = $PSScriptRoot
Set-Location $scriptloc/..

# Build the docker image
docker build --progress=plain -t ossdbtoolsservice:$BuildVersion .

# Restore the original directory
Set-Location $curloc