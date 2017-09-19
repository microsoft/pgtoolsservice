# Save the current directory and the script's directory, since tests must be run from the project root
$curloc = $pwd
$scriptloc = $PSScriptRoot
Set-Location $scriptloc/..

# Display an error if the integration test config file does not exist
if (!(Test-Path 'tests\integration\config.json'))
{
  Write-Output "Error: No integration test config file found at tests\integration\config.json. Copy config.json.txt at that location to config.json, then edit the settings as needed. See the 'Configuring Integration Tests' section in README.md for more details."
  return
}

# Run the tests
nosetests @args
Set-Location $curloc