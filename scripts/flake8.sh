#!/usr/bin/env bash
if [ ! -d 'ossdbtoolsservice' ] || [ ! -d 'tests' ] || [ ! -d 'pgsmo' ]
then
  echo "Script must be executed from root of repo"
  exit 1
fi

# Function to check if a command is available
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

pip install --upgrade pip
# Install flake8 if it's missing
if ! command_exists flake8; then
  echo "flake8 not found. Installing flake8..."
  pip3 install flake8
fi

flake8 --max-line-length=160 --ignore W605,W503,W504 --builtins psycopg,ossdbtoolsservice,View ossdbtoolsservice
flake8 --max-line-length=160 --ignore W605,W503,W504 --builtins psycopg,ossdbtoolsservice,View tests
flake8 --max-line-length=160 --ignore W605,W503,W504 --builtins psycopg,ossdbtoolsservice,View pgsmo
