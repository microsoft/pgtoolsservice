#!/usr/bin/env bash
if [ ! -d 'pgsqltoolsservice' ] || [ ! -d 'tests' ]
then
  echo "Script must be executed from root of repo"
  exit 1
fi

flake8 --max-line-length=160 pgsqltoolsservice
flake8 --max-line-length=160 tests
