# Save the current directory and the script's directory, since tests must be run from the project root
$curloc = $pwd
$scriptloc = $PSScriptRoot
Set-Location $scriptloc/..

# Run the tests and generate coverage report
python -m nose2 -v -A '!is_integration_test' --with-coverage

# Get the coverage diff
diff-cover coverage_reports/coverage.xml --compare-branch=origin/master-mysql-extension --html-report coverage_reports/coverage_diff.html

Set-Location $curloc
