#!/usr/bin/env bash

if [ ! -d 'pgsqltoolsservice' ] || [ ! -d 'tests' ]
then
  echo "Script must be executed from root of repo"
  exit 1
fi

autopep8 --in-place --aggressive --aggressive --max-line-length 160 -r .
