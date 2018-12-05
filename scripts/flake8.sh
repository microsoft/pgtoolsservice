#!/usr/bin/env bash
if [ ! -d 'pgsqltoolsservice' ] || [ ! -d 'tests' ] || [ ! -d 'pgsmo' ]
then
  echo "Script must be executed from root of repo"
  exit 1
fi

flake8 --max-line-length=160 --ignore W605,W503,W504 --builtins psycopg2,pgsqltoolsservice,View pgsqltoolsservice
flake8 --max-line-length=160 --ignore W605,W503,W504 --builtins psycopg2,pgsqltoolsservice,View tests
flake8 --max-line-length=160 --ignore W605,W503,W504 --builtins psycopg2,pgsqltoolsservice,View pgsmo