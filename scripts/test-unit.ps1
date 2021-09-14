# Save the current directory and the script's directory, since tests must be run from the project root
$curloc = $pwd
$scriptloc = $PSScriptRoot
Set-Location $scriptloc/..

# Run the tests
nosetests -a '!is_integration_test' --with-xunit @args
Set-Location $curloc
