#!/usr/bin/env bash

set -e

if [[ "${CI}" ]]; then
    set -x
fi

function usage() {
    if [[ "${1}" ]]; then
        echo "${1}"
    fi
    echo -n \
        "Usage: $(basename "$0") [OPTIONS]
Runs tests for the project.

Options
    --playback
        Run playback tests. Requires docker.
"
}

# Parse args
PLAYBACK=""
REST=()
while [[ $# -gt 0 ]]; do case $1 in
    --playback)
        PLAYBACK="--playback"
        shift
        ;;    
    --help)
        usage
        exit 0
        shift
        ;;
    *)
        REST+=("$1")
        shift
        ;;
    esac done

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
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
  
  if [ ${#REST[@]} -gt 0 ]; then
      nose2 -v --with-coverage --coverage-report html --plugin=nose2.plugins.junitxml --junit-xml "${REST[@]}"
  else
      nose2 -v --with-coverage --coverage-report html --plugin=nose2.plugins.junitxml
  fi
  pytest tests_v2 "$PLAYBACK"
fi