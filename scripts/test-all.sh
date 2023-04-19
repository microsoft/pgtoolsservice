#!/usr/bin/env bash
if [ ! -d 'ossdbtoolsservice' ] || [ ! -d 'tests' ] || [ ! -d 'pgsmo' ]
then
  echo "Script must be executed from root of repo"
  exit 1
fi

# Display an error if the integration test config file does not exist
if [ ! -f 'tests/integration/config.json' ]
then
  echo "Error: No integration test config file found at tests/integration/config.json. Copy config.json.txt at that location to config.json, then edit the settings as needed. See the 'Configuring Integration Tests' section in README.md for more details."
  exit
fi

nose2 -v --with-coverage --coverage-report html --plugin=nose2.plugins.junitxml --junit-xml "$@"
