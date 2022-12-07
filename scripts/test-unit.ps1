# Save the current directory and the script's directory, since tests must be run from the project root
$curloc = $pwd
$scriptloc = $PSScriptRoot
Set-Location $scriptloc/..

# Run the tests
python -m nose2 -v -A '!is_integration_test' --with-coverage
Set-Location $curloc
