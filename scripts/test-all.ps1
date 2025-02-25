$ErrorActionPreference = "Stop"

# Save the current directory and the script's directory, since tests must be run from the project root
$curloc = $pwd
$scriptloc = $PSScriptRoot
Set-Location $scriptloc/..

# Process arguments
$playback = ""
$restArgs = @()
foreach ($arg in $args) {
    if ($arg -eq "--playback") {
        $playback = "--playback"
    } else {
        $restArgs += $arg
    }
}

# Display an error if the integration test config file does not exist
if (!(Test-Path 'tests\integration\config.json'))
{
  Write-Output "Error: No integration test config file found at tests\integration\config.json. Copy config.json.txt at that location to config.json, then edit the settings as needed. See the 'Configuring Integration Tests' section in README.md for more details."
  return
}

# Run the tests conditionally including filtered args for nose2
if ($restArgs.Count -gt 0) {
    nose2 -v --with-coverage --coverage-report html --plugin=nose2.plugins.junitxml --junit-xml $restArgs
} else {
    nose2 -v --with-coverage --coverage-report html --plugin=nose2.plugins.junitxml --junit-xml
}
pytest tests_v2 $playback
Set-Location $curloc
