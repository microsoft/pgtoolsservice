#!/usr/bin/env bash
if [ ! -d 'ossdbtoolsservice' ] || [ ! -d 'tests' ] || [ ! -d 'mysqlsmo' ]
then
  echo "Script must be executed from root of repo"
  exit 1
fi

python3 -m nose2 -v -A '!is_integration_test' --with-coverage
