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

    echo "Running ruff check..."
    ruff check ossdbtoolsservice tests tests_v2 pgsmo

    echo "Running mypy check..."
    # Don't follow imports; we are not checking other legacy packages.
    mypy ossdbtoolsservice tests_v2

fi