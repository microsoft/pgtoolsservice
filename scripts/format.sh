#!/bin/bash

set -e

if [[ "${CI}" ]]; then
    set -x
fi

function usage() {
    echo -n \
        "Usage: $(basename "$0")
Formats code for this project.
"
}

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then

    echo "Running ruff format..."
    ruff format ossdbtoolsservice tests pgsmo
    ruff check --fix ossdbtoolsservice tests pgsmo    

fi