#!/usr/bin/env bash
if [ ! -d 'ossdbtoolsservice' ] || [ ! -d 'tests' ] || [ ! -d 'pgsmo' ]
then
  echo "Script must be executed from root of repo"
  exit 1
fi

flake8 --output-file="./flake-result1.txt" --max-line-length=160 --ignore W605,W503,W504 --builtins psycopg2,ossdbtoolsservice,View ossdbtoolsservice
flake8 --output-file="./flake-result2.txt" --max-line-length=160 --ignore W605,W503,W504 --builtins psycopg2,ossdbtoolsservice,View tests
flake8 --output-file="./flake-result3.txt" --max-line-length=160 --ignore W605,W503,W504 --builtins psycopg2,ossdbtoolsservice,View pgsmo
