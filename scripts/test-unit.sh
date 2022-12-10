#!/usr/bin/env bash
if [ ! -d 'ossdbtoolsservice' ] || [ ! -d 'tests' ] || [ ! -d 'mysqlsmo' ]
then
  echo "Script must be executed from root of repo"
  exit 1
fi

# Run the tests and generate coverage report
python3 -m nose2 -v -A '!is_integration_test' --with-coverage

# Get the coverage diff
diff-cover coverage_reports/coverage.xml --compare-branch=origin/master-mysql-extension --html-report coverage_reports/coverage_diff.html