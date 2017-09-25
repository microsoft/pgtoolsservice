#!/usr/bin/env bash
if [ ! -d 'pgsqltoolsservice' ] || [ ! -d 'tests' ] || [ ! -d 'pgsmo' ]
then
  echo "Script must be executed from root of repo"
  exit 1
fi

nosetests -a '!is_integration_test' --processes=-1 "$@"