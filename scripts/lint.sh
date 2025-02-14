#!/bin/bash

set -e

if [[ "${CI}" ]]; then
    set -x
fi

function usage() {
    echo -n \
        "Usage: $(basename "$0")
Runs linting for this project.
"
}

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then

    echo "Running flake8..."
    flake8 ossdbtoolsservice tests pgsmo
    
fi